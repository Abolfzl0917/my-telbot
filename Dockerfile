FROM python:3.11-slim

# تنظیمات محیطی
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Tehran
ENV PORT=10000

# ایجاد پوشه های مورد نیاز
WORKDIR /app

# نصب ابزارهای سیستم
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل requirements و نصب کتابخانه ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی فایل اصلی ربات
COPY bot.py .

# ایجاد پوشه های لازم
RUN mkdir -p user_sessions media_storage reported_media

# اکسپوز پورت
EXPOSE 10000

# اجرای ربات
CMD ["python", "bot.py"]
