# ColorMatch

A web-based Color Matching Management System developed using Django to streamline the recording, monitoring, and management of color matching formulations and laboratory processes.

The system replaces manual and spreadsheet-based workflows by providing centralized management of CMF records, Masterbatch formulations, Downcolor formulations, audit logs, dashboards, and reporting tools.

---

## Built With

### Backend

- Python
- Django
- Django ORM
- PostgreSQL *(recommended production database)*

### Frontend

- HTML5
- CSS3
- Bootstrap 5
- Bootstrap Icons
- JavaScript

### Libraries

- amCharts 5
- Tom Select
- Dropzone.js
- Flatpickr

---

## Project Structure

```
core/
│
├── core/
├── main/
│   ├── services/
│   ├── management/
│   ├── migrations/
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── manage.py
```

---

## Installation

### Clone the repository

```bash
git clone https://github.com/Freyze10/ColorMatch.git
```

### Navigate into the project

```bash
cd ColorMatch
```

### Create a virtual environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Apply migrations

```bash
python manage.py migrate
```

### Run the development server

```bash
python manage.py runserver
```

Open

```
http://127.0.0.1:8000
```

---

## Screenshots

> *(To add Soon.)*

Example:

```
screenshots/
    dashboard.png
    cmf_records.png
    formula_entry.png
```


## Author

**Brant Jan Abillanoza**

GitHub:
https://github.com/Freyze10
