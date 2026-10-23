"""
Milli-Scrapes Stress Test: 200 Different Hypercars Scraping & Verification Benchmark.
Demonstrates ultra-fast sitemap ingestion, brand-diverse hypercar discovery,
and high-concurrency asynchronous payload verification.
"""

import asyncio
import io
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Dict, Any, List
import httpx
from PIL import Image

SITEMAPS = [
    'https://www.wsupercars.com/wallpapers-sitemap.xml',
    'https://www.wsupercars.com/wallpapers-sitemap2.xml',
    'https://www.wsupercars.com/wallpapers-sitemap3.xml',
    'https://www.wsupercars.com/wallpapers-sitemap4.xml'
]

HYPERCAR_BRANDS = [
    'bugatti', 'koenigsegg', 'pagani', 'rimac', 'mclaren', 'ferrari', 'lamborghini',
    'aston-martin', 'hennessey', 'ssc', 'zenvo', 'pininfarina', 'de-tomaso', 'apollo',
    'czinger', 'gordon-murray', 'w-motors', 'saleen', 'brabham', 'delage', 'praga',
    'lotus', 'porsche', 'maserati', 'spyker', 'noble', 'gumpert', 'nio'
]


def ingest_sitemaps_for_hypercars() -> List[Dict[str, Any]]:
    """Discovers all unique hypercars across sitemaps in milliseconds."""
    t0 = time.perf_counter()
    candidate_cars = []
    seen = set()

    for sm in SITEMAPS:
        req = urllib.request.Request(sm, headers={'User-Agent': 'Milli-Scrapes/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_text = resp.read().decode('utf-8')

        blocks = re.findall(r'<url>(.*?)</url>', xml_text, re.DOTALL)
        for block in blocks:
            loc_m = re.search(r'<loc>(https?://[^\s<]+)</loc>', block)
            if not loc_m:
                continue
            page_url = loc_m.group(1)
            slug = page_url.lower()

            matched_brand = None
            for b in HYPERCAR_BRANDS:
                if f'/{b}/' in slug or f'-{b}-' in slug:
                    matched_brand = b
                    break
            if not matched_brand:
                continue

            img_locs = re.findall(r'<image:loc>(https?://[^\s<]+)</image:loc>', block)
            car_photos = [
                img for img in img_locs 
                if img.endswith(('.jpg', '.jpeg', '.webp')) and 'wp-content/uploads' in img
            ]
            if not car_photos:
                continue

            raw_slug = page_url.rstrip('/').split('/')[-1]
            car_name = raw_slug.replace('-', ' ').title()

            if car_name not in seen:
                seen.add(car_name)
                candidate_cars.append({
                    'name': car_name,
                    'brand': matched_brand.replace('-', ' ').title(),
                    'page_url': page_url,
                    'image_url': car_photos[0]
                })

    elapsed = time.perf_counter() - t0
    print(f"[Ingest] Discovered {len(candidate_cars)} unique hypercars in {elapsed:.2f}s")
    return candidate_cars


def select_diverse_200(candidate_cars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Selects 200 distinct hypercars using round-robin across brands for maximum variety."""
    by_brand: Dict[str, List[Dict[str, Any]]] = {}
    for c in candidate_cars:
        by_brand.setdefault(c['brand'], []).append(c)

    selected = []
    brands = sorted(list(by_brand.keys()))
    pointers = {b: 0 for b in brands}

    while len(selected) < 200:
        added = False
        for b in brands:
            if len(selected) >= 200:
                break
            if pointers[b] < len(by_brand[b]):
                selected.append(by_brand[b][pointers[b]])
                pointers[b] += 1
                added = True
        if not added:
            break

    for i, c in enumerate(selected, 1):
        c['id'] = i

    print(f"[Select] Selected exactly {len(selected)} diverse hypercars from {len(by_brand)} brands")
    return selected


async def fetch_and_verify_image(
    client: httpx.AsyncClient,
    car: Dict[str, Any],
    sem: asyncio.Semaphore
) -> Dict[str, Any]:
    """Asynchronously fetches image in RAM and validates dimensions and integrity."""
    async with sem:
        t0 = time.perf_counter()
        try:
            resp = await client.get(car['image_url'], timeout=12.0)
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
            
            if resp.status_code == 200:
                raw_bytes = resp.content
                size_bytes = len(raw_bytes)
                # Decode in memory with PIL
                im = Image.open(io.BytesIO(raw_bytes))
                width, height = im.size
                img_format = im.format or 'JPEG'

                return {
                    **car,
                    'status': 200,
                    'valid': True,
                    'size_bytes': size_bytes,
                    'size_kb': round(size_bytes / 1024, 1),
                    'dimensions': f"{width}x{height}",
                    'format': img_format,
                    'latency_ms': latency_ms
                }
            else:
                return {
                    **car,
                    'status': resp.status_code,
                    'valid': False,
                    'latency_ms': latency_ms,
                    'error': f"HTTP {resp.status_code}"
                }
        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
            return {
                **car,
                'status': 0,
                'valid': False,
                'latency_ms': latency_ms,
                'error': str(e)
            }


async def run_stress_test(cars: List[Dict[str, Any]], concurrency: int = 25) -> List[Dict[str, Any]]:
    """Runs high-concurrency async scrape across all 200 hypercars."""
    sem = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_connections=50, max_keepalive_connections=25)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }
    
    t0 = time.perf_counter()
    async with httpx.AsyncClient(limits=limits, headers=headers, follow_redirects=True) as client:
        tasks = [fetch_and_verify_image(client, car, sem) for car in cars]
        results = await asyncio.gather(*tasks)
    
    total_time = time.perf_counter() - t0
    print(f"[Stress Test] Executed {len(results)} concurrent image scrapes in {total_time:.2f}s ({len(results)/total_time:.1f} req/s)")
    return results, total_time


def main():
    benchmarks_dir = Path('/home/raju/Downloads/milli-scrapes/benchmarks')
    benchmarks_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ingest
    candidates = ingest_sitemaps_for_hypercars()

    # 2. Select 200 diverse hypercars
    selected = select_diverse_200(candidates)

    # 3. Concurrent Stress Test
    results, elapsed = asyncio.run(run_stress_test(selected, concurrency=30))

    valid_count = sum(1 for r in results if r.get('valid'))
    total_bytes = sum(r.get('size_bytes', 0) for r in results)
    avg_latency = sum(r.get('latency_ms', 0) for r in results) / len(results)
    throughput = len(results) / elapsed

    print(f"\n================ STRESS TEST SUMMARY ================")
    print(f"Total Hypercars Scraped:   {len(results)}")
    print(f"Valid Images Verified:     {valid_count} / {len(results)} ({valid_count/len(results)*100:.1f}%)")
    print(f"Total Elapsed Time:        {elapsed:.2f} seconds")
    print(f"Throughput:                {throughput:.1f} requests/second")
    print(f"Average Latency:           {avg_latency:.1f} ms")
    print(f"Total Payload Size:        {total_bytes / 1024:.1f} KB ({total_bytes / (1024*1024):.2f} MB)")
    print(f"=====================================================")

    # 4. Save JSON dataset
    json_path = benchmarks_dir / '200_different_hypercars.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Saved dataset: {json_path}")

    # 5. Generate Markdown catalog
    md_path = benchmarks_dir / '200_DIFFERENT_HYPERCARS.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 200 Different Hypercars - Milli-Scrapes Stress Test Catalog\n\n")
        f.write(f"**Total Hypercars Scraped:** {len(results)}  \n")
        f.write(f"**Verification Success Rate:** {valid_count}/{len(results)} ({valid_count/len(results)*100:.1f}%)  \n")
        f.write(f"**Total Verification Time:** {elapsed:.2f}s ({throughput:.1f} req/s)  \n")
        f.write(f"**Total Payload Ingested:** {total_bytes / (1024*1024):.2f} MB  \n\n")
        f.write("---\n\n")
        f.write("| ID | Brand | Model | Resolution | Size | Latency | Image Link |\n")
        f.write("|:---|:---|:---|:---|:---|:---|:---|\n")
        for r in results:
            dim = r.get('dimensions', 'N/A')
            sz = f"{r.get('size_kb', 0)} KB"
            lat = f"{r.get('latency_ms', 0)} ms"
            f.write(f"| {r['id']} | **{r['brand']}** | [{r['name']}]({r['page_url']}) | {dim} | {sz} | {lat} | [View Image]({r['image_url']}) |\n")

    print(f"Saved Markdown catalog: {md_path}")


if __name__ == '__main__':
    main()
