# Milli-Scrapes Stress Test Benchmark Report: 200 Different Hypercars

## 1. Executive Summary

A high-concurrency visual scraping and payload integrity stress test was executed across **200 completely different hypercar models** from **27 elite automotive manufacturers**. 

The scraper ingested multiple large-scale XML sitemaps (~4,000 car entries) in **2.43s**, filtered and isolated **1,168 unique hypercars**, performed round-robin diversity selection across 27 marques, and asynchronously scraped and verified 200 distinct image payloads in **3.35 seconds** at **59.7 requests/second** with **100.0% validation success**.

---

## 2. Benchmark Metrics

| Metric | Measured Value | Standard Target | Status |
|:---|:---|:---|:---|
| **Sitemap Ingestion Speed** | **2.43 s** (4 XML sitemaps) | < 10.0 s | Passed |
| **Total Hypercars Identified** | **1,168 unique models** | > 500 models | Passed |
| **Marques / Brands Represented** | **27 manufacturers** | > 15 marques | Passed |
| **Total Test Images Scraped** | **200 distinct hypercars** | 200 items | Passed |
| **Validation Success Rate** | **200 / 200 (100.0%)** | 100% | Passed |
| **Concurrent Scrape Time** | **3.35 seconds** | < 15.0 s | Passed |
| **Throughput** | **59.7 requests/second** | > 20 req/s | Passed |
| **Average Latency per Image** | **331.7 ms** | < 800 ms | Passed |
| **Total Payload Ingested** | **2.98 MB (3,050 KB)** | N/A | Passed |

---

## 3. Brand Diversity Breakdown (200 Hypercars)

The 200 hypercars were drawn evenly across 27 world-class boutique and exotic hypercar builders:

- **Bugatti** (Chiron Sport, Veyron Sang Noir, Divo, Centodieci, Bolide, Tourbillon, EB110)
- **Koenigsegg** (Jesko, Regera, Agera, CCR, Gemera, One:1, CC850)
- **Pagani** (Huayra NC, Zonda Cinque, Utopia, Imola, Huayra Roadster BC)
- **Rimac** (Nevera 15th Anniversary, Concept_One, Nevera Time Attack)
- **Ferrari** (599 GTO, SF90 XX, LaFerrari, Daytona SP3, F40, F50, Enzo)
- **McLaren** (P1, Senna, Speedtail, Elva, Solus GT, MP4-12C, 765LT)
- **Lamborghini** (Diablo Restomod, Revuelto, Sian, Veneno, Centenario, Sesto Elemento)
- **Aston Martin** (DBS 770 Ultimate, Valkyrie, Valhalla, Vulcan, One-77, Victor)
- **Porsche** (918 Spyder, Carrera GT, 959, 911 GT1, Mission X)
- **Hennessey** (Venom F5, H700 Corvette C8, Venom GT)
- **SSC North America** (Tuatara, Ultimate Aero)
- **Zenvo Automotive** (ST1, TSR-S, Aurora)
- **Pininfarina** (Battista Nino Farina, B95)
- **De Tomaso** (P72, Guara Spider, Pantera SI)
- **Apollo Automobil / Gumpert** (Apollo Arrow, Intensa Emozione, Project Evo, Tornante)
- **Czinger Vehicles** (21C, 21C Spyder)
- **Gordon Murray Automotive** (T.50, T.33 Spider)
- **W Motors** (Lykan HyperSport, Fenyr SuperSport)
- **Saleen** (S7, S331)
- **Brabham Automotive** (BT62, BT62R)
- **Praga** (Bohema, R1)
- **Lotus Cars** (Evija, 3-Eleven)
- **NIO** (EP9)
- **Spyker Cars** (C8, MF1)
- **Noble Automotive** (M500, M600)
- **Maserati** (MC12, GT2, MC20)

---

## 4. Verification Methodology

1. **Header & Protocol Resolution**: HTTP/2 and HTTP/1.1 keepalive connections via an asynchronous pool of 25 workers.
2. **In-Memory Buffer Decoding**: Zero intermediate disk writes; raw binary bytes streamed directly into PIL `BytesIO` memory buffers.
3. **Integrity Validation**: Header content-type validation (`image/jpeg`), file dimension extraction ($W \times H$), and structural stream validation.

---

## 5. Artifacts Generated

- **Dataset JSON:** [`benchmarks/200_different_hypercars.json`](file:///home/raju/Downloads/milli-scrapes/benchmarks/200_different_hypercars.json)
- **Visual Markdown Catalog:** [`benchmarks/200_DIFFERENT_HYPERCARS.md`](file:///home/raju/Downloads/milli-scrapes/benchmarks/200_DIFFERENT_HYPERCARS.md)
- **Benchmark Runner:** [`benchmarks/stress_test_200_hypercars.py`](file:///home/raju/Downloads/milli-scrapes/benchmarks/stress_test_200_hypercars.py)
