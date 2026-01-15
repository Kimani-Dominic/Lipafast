#  Note:- Insert this dockerfile in the root of the project;
#  Lipafast is a package inside the project. and will throw errors if not run as such.

FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY lipafast/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy the package
COPY lipafast ./lipafast

RUN mkdir -p /data

# Environment variable for DB location
ENV DB_PATH=/data/db.json

# Expose FastAPI port
EXPOSE 8000

# Run as a module (IMPORTANT)
CMD ["python", "-m", "lipafast.main"]
