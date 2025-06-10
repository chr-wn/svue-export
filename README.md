# StudentVUE Grade Exporter

A Python script for exporting exact assignments and grades from StudentVUE into a single CSV file because they disappear when the school year ends.

---

### Setup

**1. Prerequisites**
Ensure python3 and pip are installed. 

**2. Get the Code**
Clone or download this repo.

```bash
git clone <repository_url>
cd <repository_directory>
```

**3. Install Dependencies**
This project uses a few external libraries. Install them using pip (this makes a venv too):

```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

**4. Configure Credentials**
For security, credentials are read from a local environment file. Create a file named `.env` in the project directory.

Add your credentials to it, following this format:
```
STUDENTVUE_USERNAME="your_username_here"
STUDENTVUE_PASSWORD="your_password_here"
```

---

### Usage

Once the setup is complete, run the script from your terminal:

```bash
python main.py
```

The script first attempts to load credentials from `.env` file. If file not found, it will prompt for user credentials directly in terminal.

When finished, a `grades.csv` file will be created, containing all courses and assignments.
