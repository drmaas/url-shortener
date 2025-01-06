# URL Shortening Service

## Context

This service allows users to shorten long URLs, making them easier to share and use.

## Functional Requirements

*   The service shall accept a long URL as input from the user (via web UI or API).
*   The service shall validate the input URL format.
*   The service shall generate a unique, short code (e.g., `bdds8utd`).
*   The short code shall be less than 10 characters.
*   The service shall store the mapping between the short code and the original long URL.
*   The service shall return the complete shortened URL (including the base URL of the service, e.g., `https://tinyurl.com/bdds8utd`) to the user.
*   The service shall accept a short code as input.
*   The service shall retrieve the corresponding long URL from storage.
*   The service shall return the original long URL.
*   When a user accesses a shortened URL, the service shall resolve the short code.
*   The service shall perform an HTTP 301 (Permanent Redirect) or 302 (Temporary Redirect) to the corresponding long URL.
*   The service shall increment a click counter associated with the short code.
*   If the short code is not found, the service shall return an HTML error page with an appropriate HTTP status code (e.g., 404 Not Found) and an error message.
*   The service shall store click data (e.g., timestamp, IP address (with privacy considerations), referrer) for each redirect.
*   The service shall provide an interface (e.g., API endpoint, web UI) for retrieving click statistics for a given short code.
*   The service shall allow users to request custom short codes (if available).
*   The service shall validate the requested custom short code (e.g., length, allowed characters, availability).
*   The API shall use JSON for request and response bodies.

## Non-functional requirements

*   **Performance:**
    *   **Latency:** The service should redirect users to the original URL within 200ms (milliseconds) on average.
    *   **Throughput:** The service should be able to handle at least 10,000 URL shortening requests during peak hours.
*   **Scalability:** The system should be designed to handle increasing traffic and storage requirements. We should be able to easily scale the system horizontally by adding more servers or database capacity.
*   **Availability:** The service should be available 99.9% of the time (three nines). This translates to approximately 43 minutes of downtime per month.
*   **Security:**
    *   The service should prevent unauthorized access to the database.
    *   The service should protect against common web vulnerabilities such as Cross-Site Scripting (XSS) and SQL Injection.
*   **Privacy:**
    *   IP addresses should be anonymized or hashed before storage to protect user privacy.
    *   Users should be informed about what data is collected and how it is used.
*   **Storage:** The service should be able to store at least 3.6 million URL mappings and associated click data.
*   **Maximum URL Length:** The service should support long URLs up to 2,000 characters.

## Use Cases

*   A user wants to shorten a long URL and share it on social media.
*   A developer wants to integrate the URL shortening service into their application using an API.
*   A marketing team wants to create custom short links with branded domains or keywords.
*   A marketer uses the service to shorten URLs used in marketing campaigns and track click-through rates.
*   A business wants to generate QR codes for physical marketing materials using shortened URLs.

## Exclusions

*(To be defined)*

## Implementation Details

*   We will use AWS Lambda for our compute needs.
*   We will use separate Lambda functions for each major operation.
*   We will use Amazon API Gateway to create the API endpoints and integrate with Lambda.

### Lambda Functions

*   **Memory Allocation:** 128 MB per function (initially).

#### `shortenUrl` Lambda Function

*   Handles URL shortening requests.
*   Validates input.
*   Generates short code.
*   Writes to DynamoDB.

#### `redirectUrl` Lambda Function

*   Handles redirect requests.
*   Reads from DynamoDB.
*   Performs redirects.
*   Increments click counter.
*   Handles 404s.

#### `getOriginalUrl` Lambda Function

*   Handles requests to get the original URL from a short code.
*   Reads from DynamoDB.
*   Returns the original URL.

#### `getClickStats` Lambda Function

*   Handles requests to get click statistics.
*   Queries the click data table in DynamoDB.
*   Returns the statistics.

### Short Code Generation

*   We will use random string generation with collision checking.
*   Short codes will be 8 characters long, using a base62 character set (a-z, A-Z, 0-9).
*   The generation process will check for collisions in the DynamoDB table and regenerate the code if necessary.

### Data Model

We will use Amazon DynamoDB as our database.

#### URL Mapping Table

| Attribute    | Type    | Description                                       |
| :----------- | :------ | :------------------------------------------------ |
| `short_code` | String  | Primary Key (Partition Key), Unique short code.   |
| `long_url`   | String  | The original long URL.                            |
| `created_at` | Number  | Timestamp of creation.                           |
| `clicks`     | Number  | Click counter.                                    |
| `custom`     | Boolean | Flag indicating if short code was custom or not. |

#### Click Data Table

| Attribute       | Type    | Description                                             |
| :-------------- | :------ | :------------------------------------------------------ |
| `short_code`    | String  | Partition Key, The short code.                         |
| `click_timestamp` | Number  | Sort Key, The timestamp of the click.                 |
| `ip_hash`       | String  | A hashed version of the user's IP address.            |
| `referrer`      | String  | The referring URL.                                    |

### Input Validation

*   The service shall validate that the input URL is a valid URL format (using regular expressions or a URL parsing library).
*   The service shall reject URLs longer than 2,000 characters.

### Storage Estimates

*   Estimated URL mapping storage: ~1.4 GB per year.
*   Estimated click data storage: ~1.6 GB per year.
*   **Total estimated storage:** ~3 GB per year.
*   Estimated time within 25 GB free tier: ~8 years.

### Storage Management Strategies

*   Archive or delete older click data.
*   Aggregate click data into summaries.
*   Monitor DynamoDB costs and evaluate alternative storage options if needed.

## Observability

*(To be defined)*

## Privacy and Security

*(To be defined)*

## Deployment

*(To be defined)*

## API

The API has the following endpoints:

1.  `POST /url` - A `POST` endpoint to shorten a URL. Accepts a JSON payload with the `longUrl` field. Returns a JSON payload with the `shortUrl` field.
2.  `GET /{shortCode}` - A `GET` endpoint to redirect to the original URL.
3.  `GET /url/{shortCode}` - A `GET` endpoint to get the original URL from a short code. Returns a JSON payload with the `longUrl` field.
4.  `GET /stats/{shortCode}` - A `GET` endpoint to get click statistics for a short code. Returns a JSON payload with statistics.

## Style Guide

Our organization follows these principles for development.

*   DRY
*   SOLID
*   TDD

Our company follows these coding styles and best practices:


- Use Python `black` formatting.
- Use Python type hints.
- Pytest for testing.
- Testing:
    - All business use cases should be covered in the tests.
    - Focus testing on business case functional testing to test at API
      boundaries such as REST APIs -- not class-level
      tests.
    - For fake data use "example" in the name. "test" must only be used for the
      test names themselves.
    - If monkey-patching or other dependency injection is necessary, only do so
      in pytest fixtures -- no dependency
      injection in tests themselves.
    - Use testing analogs for external dependencies like databases. Do not use
      test analogs for our own code.
    - Testing analogs should function the same as the libraries and services
      they mimic. Only implement as much analog
      functionality as needed for the test.
    - For test analogs, use "fake" in the name.