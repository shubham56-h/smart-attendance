# PostgreSQL Migration Guide

## Local Development Setup

### 1. Install PostgreSQL
- **Windows**: Download from https://www.postgresql.org/download/windows/
- **Mac**: `brew install postgresql`
- **Linux**: `sudo apt-get install postgresql postgresql-contrib`

### 2. Create Database
```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE attendance_db;

# Exit
\q
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables
Create a `.env` file (copy from `.env.example`):
```bash
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/attendance_db
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### 5. Run Migrations
```bash
# Initialize migrations (if not already done)
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### 6. Migrate Data from SQLite (Optional)
If you have existing data in SQLite:
```bash
# Update connection details in migrate_to_postgres.py
python migrate_to_postgres.py
```

### 7. Run the Application
```bash
python run.py
```

---

## Production Deployment (Render/Railway/Heroku)

### Option 1: Render.com

1. **Create PostgreSQL Database**
   - Go to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Name: `attendance-db`
   - Copy the "Internal Database URL"

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn run:app`
   
3. **Add Environment Variables**
   - `DATABASE_URL`: (paste the Internal Database URL)
   - `SECRET_KEY`: (generate random string)
   - `JWT_SECRET_KEY`: (generate random string)
   - `PYTHON_VERSION`: `3.11.0`

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment

### Option 2: Railway.app

1. **Create New Project**
   - Go to Railway Dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"

2. **Add PostgreSQL**
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL`

3. **Configure Service**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`

4. **Add Environment Variables**
   - `SECRET_KEY`: (generate random string)
   - `JWT_SECRET_KEY`: (generate random string)

5. **Deploy**
   - Push to GitHub
   - Railway auto-deploys

### Option 3: Heroku

1. **Create App**
```bash
heroku create your-app-name
```

2. **Add PostgreSQL**
```bash
heroku addons:create heroku-postgresql:mini
```

3. **Set Environment Variables**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set JWT_SECRET_KEY=your-jwt-secret-key
```

4. **Deploy**
```bash
git push heroku main
```

5. **Run Migrations**
```bash
heroku run flask db upgrade
```

---

## Important Notes

### For Production:
1. **Add gunicorn** to requirements.txt:
   ```
   gunicorn
   ```

2. **Create Procfile** (for Heroku):
   ```
   web: gunicorn run:app
   ```

3. **Security**:
   - Never commit `.env` file
   - Use strong SECRET_KEY and JWT_SECRET_KEY
   - Enable SSL/HTTPS in production

4. **Database URL Format**:
   - Some platforms use `postgres://` instead of `postgresql://`
   - Add this to handle both:
   ```python
   database_url = os.environ.get('DATABASE_URL')
   if database_url and database_url.startswith('postgres://'):
       database_url = database_url.replace('postgres://', 'postgresql://', 1)
   ```

### Troubleshooting:
- **Connection refused**: Check PostgreSQL is running
- **Authentication failed**: Verify username/password
- **Database doesn't exist**: Create it first with `CREATE DATABASE`
- **Migration errors**: Delete migrations folder and reinitialize
