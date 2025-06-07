woo-rial-fixer

Python script to correct Rial pricing on Iranian WooCommerce stores and send confirmation emails.

🔍 Overview

woo-rial-fixer connects to your WooCommerce-powered store, normalizes product prices to Iranian Rial (IRR), and sends you a summary email upon completion.

Key features:

Fetch products from your WooCommerce store and put them in an excel sheet

Fetch USD rate from [tgju] (https://www.tgju.org/profile/price_dollar_rl

Convert and fix prices to IRR

Update prices in WooCommerce via the REST API

Send a confirmation email with a summary of changes

🚀 Prerequisites

Python 3.8 or higher

Access to a WooCommerce store with REST API credentials

SMTP credentials for sending email

🛠️ Installation

Clone the repository

git clone https://github.com/aminvahdat/woocommerce-iran-price-fix.git
cd woocommerce-iran-price-fix

Create a virtual environment

python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

Install dependencies

pip install -r requirements.txt

⚙️ Configuration

Copy the example environment file

cp env.example .env

Open .env and fill in your credentials:

# WooCommerce API
WC_URL=https://your-store.ir
WC_CONSUMER_KEY=ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WC_CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# SMTP for confirmation email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=your-email-password
EMAIL_TO=notify-me@example.com

▶️ Usage

Run the script with:

python update_prices.py

On success, you'll see a summary in the console and receive an email with details of the updated prices.

🤝 Contributing

Contributions, issues, and feature requests are welcome!

Fork the project

Create your feature branch: git checkout -b feature/your-feature

Commit your changes: `git commit -m "Add your feature"

Push to the branch: git push origin feature/your-feature

Open a pull request

📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

📞 Contact

Created by Amin (t.me/a_aminam). Feel free to reach out with any questions or suggestions.

