FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot code
COPY bot.py .

# Set environment variables (replace with actual values)
ENV BOT_TOKEN="your-telegram-bot-token-here"
ENV API_URL_TEMPLATE="your-api-url-template-here"
ENV WEBHOOK_URL="https://your-webhook-url-here.com/"
ENV PORT=5000
ENV TZ=Asia/Kolkata

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Start the bot
CMD ["python", "bot.py"]