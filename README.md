## Excel ERPNext

Extensions for Excel Technologies

# ERPNext Performance Report: 

<img width="1075" height="848" alt="image" src="https://github.com/user-attachments/assets/5e8f5550-c7fc-4f9d-942b-70e32a6566f1" />


# Load Testing Report

## Test Setup

| Option       | Value                                                      | Explanation                               |
|--------------|------------------------------------------------------------|-------------------------------------------|
| `-n`         | 1,000,000 requests total                                   | Total number of GET requests              |
| `-c`         | 50 concurrent workers                                      | 50 simulated users at the same time       |
| `-m GET`     | HTTP method used                                           | Using HTTP GET method                     |
| `URL`        | `https://dev-erp.arcapps.org/api/method/version`          | Endpoint being tested                     |

---

## Summary Results

| Metric             | Value                | Explanation                                             |
|--------------------|----------------------|---------------------------------------------------------|
| Total time         | 2165.19s (~36 minutes) | Time taken to complete 1 million requests             |
| Requests/sec       | 461.85 req/sec       | Throughput rate                                         |
| Fastest            | 0.0643s              | Fastest single request                                  |
| Slowest            | 4.9192s              | Slowest single request                                  |
| Average            | 0.1076s              | Mean time per request                                   |
| Total data         | 4875 bytes           | Total response body size received                      |
| Size/request       | 0 bytes              | Possibly zero due to minimal response payload or issue |

---

## Response Time Histogram

| Time Range (sec) | Count     | Interpretation                                  |
|------------------|-----------|--------------------------------------------------|
| 0.064 – 0.550    | 994,310   | Majority of requests responded within 0.5s      |
| 0.550 – 1.035    | 2,428     | Normal latency range                            |
| 1.035 – 4.919    | ~3,200    | Slow responses due to network or backend issues |
| > 4.919          | 1         | One extreme outlier                             |

Most requests (~99.4%) were served under 1 second.

---

## Latency Distribution (Percentiles)

| Percentile | Latency     | Meaning                                  |
|------------|-------------|------------------------------------------|
| 10%        | 0.0817s     | 10% of requests finished under 82ms      |
| 25%        | 0.0867s     | 25% under 87ms                            |
| 50% (Median)| 0.0950s    | 50% under 95ms                            |
| 75%        | 0.1049s     | 75% under 105ms                           |
| 90%        | 0.1206s     | 90% under 121ms                           |
| 95%        | 0.1457s     | 95% under 146ms                           |
| 99%        | 0.3201s     | 99% under 320ms                           |

---

## Detailed Timing Breakdown

| Metric        | Avg        | Fastest   | Slowest   | Notes                                       |
|---------------|------------|-----------|-----------|---------------------------------------------|
| DNS+dialup    | 0.0000s    | 0.0643s   | 4.9192s   | Most connections reused                     |
| DNS-lookup    | 0.0000s    | 0.0000s   | 0.0685s   | Negligible DNS lookup time                  |
| Request write | 0.0000s    | 0.0000s   | 0.0012s   | Minimal time writing the request            |
| Response wait | 0.1075s    | 0.0642s   | 4.9191s   | Primary component of latency                |
| Response read | 0.0001s    | 0.0000s   | 0.4496s   | Response body read was very fast            |

---

## Status Code Distribution

| Status Code | Count     | Meaning                                                  |
|-------------|-----------|----------------------------------------------------------|
| 200 OK      | 999,675   | Successful responses                                     |
| 502 Bad Gateway | 325   | Backend or reverse proxy failed to serve the request    |

---

## Analysis & Observations

### What Went Well
- Excellent latency performance — 99% of responses were under 320ms.
- High success rate — 99.97% of the requests received a 200 OK.
- Server sustained a steady load with 50 concurrent users for over 36 minutes.

### Minor Issues
- 325 failed requests with 502 errors suggest occasional reverse proxy issues.
- Total data transferred (4875 bytes) seems suspiciously low for 1 million requests — likely due to:
  - Minimal payload from the endpoint.
  - Logging/reporting limitation in `hey`.

# Another Performance Report:

<img width="1125" height="944" alt="image" src="https://github.com/user-attachments/assets/9f3ca1e4-e08f-4e5d-82c7-ca5bc829fa22" />


# Individual Container Scalup Report: 

<img width="1572" height="749" alt="image" src="https://github.com/user-attachments/assets/e932072f-b1a4-40d3-ad36-70ad2a48a351" />

