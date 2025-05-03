import requests
from bs4 import BeautifulSoup

def scrape_jd_from_url(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    # Heuristics for common job boards
    selectors = [
        {"tag": "div", "class": "content"},      # Lever
        {"tag": "section", "class": "postings-section"},  # Greenhouse
        {"tag": "div", "class": "jobs-posting"},  # LinkedIn
    ]

    for sel in selectors:
        container = soup.find(sel["tag"], class_=sel["class"])
        if container:
            text = container.get_text(separator="\n")
            return text.strip()

    # Fallback: full page text
    return soup.get_text(separator="\n").strip()

if __name__ == "__main__":
    url = "https://www.indeed.com/viewjob?jk=54deff04f23e5118&tk=1ip4joh5l2cki001&from=hpd.jobsForYou&vjs=3&advn=7326412386046683&adid=433149018&ad=-6NYlbfkN0BWpgndjYL01xMr26yTqLCDFb3b3BUdaEwmMV3w6lpNxUsIZLXemk5fkggRKKneAdNGicOy2fSZ5X3rZRw5x5_JB2enKWIDg6RZaeDCRhsZEnhWj9bxMJohKKE41z3vjiA842whxI9Kld-oaK0yu9zLVpNLwBO-h_BuHfCcSKaZVHxpcSamt2EfH2glVFsQCPZ-NYDKcnU7Sv9E7jdxmI3gLPMObmE-V-N95lCiiJpUF255bJV8u3BplUyyzp01mZZ0iV1mJvCpQEgDvTlqQNDAEij1-b6hJeqI3lsGiy7ov8iQ-ROAl69M6Cn0Va64oaX8vSjIb_ntq-i5cFBKeQrV7_R224A5btIgkKQVqvy_pbWXiUUKQTqcpFqoe26hUsmZSFb-tnUMr7eTuaYOa7P54lmsbeW8lCTj6jQ44ipoHjlFgoqag07BZ3-xwoJ1zl8sJ6J9iNHKRr9I6ZgqEnhTWZzutSvOKjI59N_4Iq7X_SAsdxSwFjgEmgQG2JOSbtiNnmymvGlUv3ebbtPib9Rive6aTUTyyK0v590zMpd6uzJ3pHYDQDJCdZuxFueqnpaXtUCTaUiiczc0ixfrcz_yh63UKLAqBYQ=&xkcb=SoCh6_M3zkvut0S0450ObzkdCdPP&xpse=SoDZ6_I3zkvt_vgM870IbzkdCdPP&sjdu=QWF4TUFyrHvH7u082A4fazNo9p3LIzRcrlYzDN8MBDg"
    job_description = scrape_jd_from_url(url)
    print(job_description)