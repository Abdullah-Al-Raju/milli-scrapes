import pytest
from milli_scrapes.extractor.lead_verifier import MilliLeadVerifier

def test_cloudflare_email_decoder():
    # Simulated encoded email: 'info@testrestaurant.com' with key 0x5a
    email = "info@testrestaurant.com"
    key = 0x5a
    cf_hex = f"{key:02x}" + "".join(f"{(ord(c) ^ key):02x}" for c in email)
    
    decoded = MilliLeadVerifier.decode_cloudflare_email(cf_hex)
    assert decoded == email

def test_extract_cloudflare_emails_from_html():
    email = "contact@bistro.fr"
    key = 0x33
    cf_hex = f"{key:02x}" + "".join(f"{(ord(c) ^ key):02x}" for c in email)
    html = f'''
    <div>
        <a href="/cdn-cgi/l/email-protection#{cf_hex}" class="__cf_email__" data-cfemail="{cf_hex}">[email&#160;protected]</a>
    </div>
    '''
    extracted = MilliLeadVerifier.extract_cloudflare_emails(html)
    assert extracted == [email]

def test_deobfuscate_human_anti_spam_emails():
    text = "Feel free to reach out to us at contact [at] pizzanapoli [dot] it for catering bookings."
    emails = MilliLeadVerifier.deobfuscate_text_emails(text)
    assert "contact@pizzanapoli.it" in emails

def test_extract_schema_json_ld():
    html = '''
    <html>
    <head>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Restaurant",
      "name": "Trattoria Milano",
      "telephone": "+39 02 1234567",
      "email": "prenotazioni@trattoriamilano.it",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "Via Monte Napoleone 8",
        "addressLocality": "Milano",
        "postalCode": "20121",
        "addressCountry": "IT"
      },
      "sameAs": [
        "https://www.facebook.com/trattoriamilanoofficial",
        "https://www.instagram.com/trattoria_milano/"
      ]
    }
    </script>
    </head>
    <body><h1>Benvenuti</h1></body>
    </html>
    '''
    res = MilliLeadVerifier.extract_schema_json_ld(html)
    assert "prenotazioni@trattoriamilano.it" in res["emails"]
    assert "+39021234567" in res["phones"] or "+39 02 1234567" in res["phones"]
    assert res["social_media"].get("instagram") == "https://instagram.com/trattoria_milano"
    assert res["social_media"].get("facebook") == "https://facebook.com/trattoriamilanoofficial"
    assert "Via Monte Napoleone 8" in res["address"]

def test_extract_meta_contacts():
    html = '''
    <html>
    <head>
    <meta property="og:phone_number" content="+1 (206) 555-0199" />
    <meta property="og:email" content="orders@seattlecoffee.com" />
    <meta name="twitter:site" content="@seattlecoffee" />
    </head>
    </html>
    '''
    meta = MilliLeadVerifier.extract_meta_contacts(html)
    assert "+1-206-555-0199" in meta["phones"] or "+12065550199" in meta["phones"]
    assert "orders@seattlecoffee.com" in meta["emails"]
    assert meta["social_media"].get("twitter_x") == "https://x.com/seattlecoffee"

def test_phone_normalization_and_validation():
    # Valid US phone
    assert MilliLeadVerifier.normalize_phone_number("206-555-0123") == "+1-206-555-0123"
    # Valid international with +
    assert MilliLeadVerifier.normalize_phone_number("+39 02 8888 9999") == "+390288889999"
    # Reject dummy all-zero digits
    assert MilliLeadVerifier.normalize_phone_number("0000000000") is None
    # Reject timestamps / years
    assert MilliLeadVerifier.normalize_phone_number("20261030") is None
    # Reject short strings
    assert MilliLeadVerifier.normalize_phone_number("12345") is None

def test_enrich_contacts_consolidation():
    raw_html = '''
    <html>
    <head>
    <meta property="og:email" content="press@acme.org" />
    </head>
    <body>
    <p>General inquiries: info [at] acme [dot] org</p>
    </body>
    </html>
    '''
    enriched = MilliLeadVerifier.enrich_contacts(raw_html, enable_dns_osint=False)
    assert "info@acme.org" in enriched["emails"]
    assert "press@acme.org" in enriched["emails"]
    assert isinstance(enriched["social_media"], dict)
