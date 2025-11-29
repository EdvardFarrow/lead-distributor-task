[![CRM Test Task CI](https://github.com/EdvardFarrow/lead-distributor-task/actions/workflows/ci.yml/badge.svg)](https://github.com/EdvardFarrow/lead-distributor-task/actions/workflows/ci.yml)

[![ru](https://img.shields.io/badge/lang-ru-grey.svg)](README_ru.md)

# 🎯 CRM Lead Distributor Service

A FastAPI-based microservice for automatically distributing incoming leads among operators.
Implements a smart request routing algorithm based on **weights** (marketing competencies) and the current **workload** of operators.

## 🚀 Key Features

* **Asynchronous:** Fully asynchronous stack (`FastAPI`, `SQLAlchemy`, `aiosqlite`) for high I/O performance. * **SQL Optimization:** Calculating the current operator load (Count Open Tickets) and selecting candidates occurs in **one** SQL query (using LEFT JOIN and DB-side aggregation).
* **Data Security:** Handling **Race Conditions** when creating leads (using 'flush' and intercepting 'IntegrityError').
* **Modern Python:** Using Python 3.11+, Pydantic v2, lifespan events.
* **CI/CD:** Configured GitHub Actions pipeline for automatic test execution.

## 🛠 Technical Stack

* **Language:** Python 3.11
* **Framework:** FastAPI
* **Database:** SQLite (Async) via SQLAlchemy 2.0
* **Testing:** Pytest, AsyncClient (httpx), In-memory DB
* **Infra:** Docker, Docker Compose

---

## 🧠 Distribution Algorithm

The request distribution logic (`POST /interactions/`) is implemented as follows:

1. **Lead Identification:** The system searches for a lead by `external_id`. If it doesn't find one, it creates a new one (with protection against duplicates during concurrent queries).
2. **Operator Analysis (Single Query):**
  * A single query selects all operators associated with a given Source.
  * Each operator's current workload (the number of tickets with the 'OPEN' status) is "joined" to them.
3. **Filtering:**
  * Inactive operators ('is_active=False') are excluded.
  * Operators with 'current_load >= max_load' are excluded.
4. **Selection (Weighted Random):**
  * A weighted random selection ('random.choices') is made among the remaining candidates.
  * The higher the operator's weight for a given source, the higher the probability of assignment.
5. **Commit:** An 'Interaction' is created, linked to the selected operator.

If there are no suitable operators, the ticket is created without an operator ('operator_id=None').

---

## 📦 Running the Project

### Via Docker (Recommended)

```bash
# Build and Run
docker-compose up --build
```

The service will be available at: http://localhost:8000 Documentation (Swagger): http://localhost:8000/docs

### Running Locally (Without Docker)

```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```
## 🧪 Testing

The project is covered with asynchronous integration tests. An isolated in-memory database is used, which is recreated for each test.

## To run tests locally:

```bash
pytest -v
```

## 📂 Project Structure

* app/main.py — Entry point, routing, lifespan.

* app/services.py — Business logic and complex SQL queries.

* app/models.py — SQLAlchemy models.

* app/schemas.py — Pydantic schemas (validation).

* app/database.py — Database engine configuration.

* tests/ — API and scenario tests.
