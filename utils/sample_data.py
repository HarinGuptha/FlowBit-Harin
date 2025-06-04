"""
Sample data generator for testing the multi-agent system.
Creates realistic sample emails, JSON webhooks, and PDF content.
"""
import json
import random
from datetime import datetime, timedelta
from faker import Faker
from typing import Dict, Any, List

fake = Faker()


class SampleDataGenerator:
    """Generate realistic sample data for testing."""
    
    def __init__(self):
        self.email_templates = {
            "complaint": [
                "I am extremely disappointed with your service. The product I received was defective and your customer service has been unhelpful. I demand a full refund immediately or I will be forced to take legal action.",
                "This is unacceptable! I've been waiting for 3 weeks for my order and still nothing. Your company is a joke and I'm reporting you to the Better Business Bureau.",
                "I am writing to express my frustration with the poor quality of service I received. The staff was rude and unprofessional. I expect better from your company."
            ],
            "rfq": [
                "We are interested in obtaining a quote for 500 units of your premium widget. Please provide pricing, delivery timeline, and payment terms.",
                "Could you please send us a quotation for your consulting services? We need a team of 3 consultants for a 6-month project starting next quarter.",
                "Request for quote: We need 1000 custom printed t-shirts with our logo. Please include setup costs and bulk pricing options."
            ],
            "invoice": [
                "Please find attached invoice #INV-2024-001 for services rendered in January. Total amount due is $5,250.00. Payment terms are Net 30.",
                "Invoice #12345 for consulting services is now due. Amount: $12,500.00. Please remit payment within 15 days to avoid late fees.",
                "Your monthly subscription invoice is ready. Invoice #SUB-2024-02 for $299.99 is due on March 1st, 2024."
            ]
        }
        
        self.compliance_keywords = {
            "GDPR": ["personal data", "data protection", "consent", "right to be forgotten"],
            "HIPAA": ["protected health information", "medical records", "patient data"],
            "SOX": ["financial reporting", "internal controls", "audit"],
            "FDA": ["clinical trial", "medical device", "drug approval"]
        }
    
    def generate_sample_email(self, intent: str = None) -> str:
        """Generate a sample email."""
        if not intent:
            intent = random.choice(["complaint", "rfq", "invoice"])
        
        sender = fake.email()
        recipient = fake.email()
        subject_prefixes = {
            "complaint": ["Complaint about", "Issue with", "Problem regarding"],
            "rfq": ["Request for Quote", "RFQ:", "Quotation Request"],
            "invoice": ["Invoice", "Payment Due", "Billing Statement"]
        }
        
        subject = f"{random.choice(subject_prefixes.get(intent, ['Re:']))} {fake.catch_phrase()}"
        body = random.choice(self.email_templates.get(intent, ["Generic email content."]))
        
        # Add some randomness to the body
        if random.random() > 0.5:
            body += f"\n\nOrder ID: {fake.uuid4()[:8].upper()}"
        
        if random.random() > 0.7:
            body += f"\nPhone: {fake.phone_number()}"
        
        email_content = f"""From: {fake.name()} <{sender}>
To: {fake.name()} <{recipient}>
Subject: {subject}
Date: {fake.date_time_between(start_date='-30d', end_date='now').strftime('%a, %d %b %Y %H:%M:%S %z')}

{body}

Best regards,
{fake.name()}
{fake.company()}
{fake.phone_number()}
"""
        return email_content
    
    def generate_sample_json(self, schema_type: str = "webhook") -> Dict[str, Any]:
        """Generate sample JSON data."""
        if schema_type == "webhook":
            return {
                "event_type": random.choice(["user_signup", "payment_completed", "order_created", "user_login"]),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": {
                    "user_id": fake.uuid4(),
                    "amount": round(random.uniform(10.0, 1000.0), 2),
                    "currency": random.choice(["USD", "EUR", "GBP"]),
                    "transaction_id": fake.uuid4()
                },
                "metadata": {
                    "source": "api",
                    "version": "1.0",
                    "ip_address": fake.ipv4()
                }
            }
        
        elif schema_type == "invoice":
            line_items = []
            for _ in range(random.randint(1, 5)):
                quantity = random.randint(1, 10)
                unit_price = round(random.uniform(10.0, 500.0), 2)
                line_items.append({
                    "description": fake.catch_phrase(),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total": round(quantity * unit_price, 2)
                })
            
            subtotal = sum(item["total"] for item in line_items)
            tax = round(subtotal * 0.08, 2)  # 8% tax
            
            return {
                "invoice_number": f"INV-{fake.year()}-{fake.random_int(min=1000, max=9999)}",
                "date": fake.date_between(start_date='-30d', end_date='today').isoformat(),
                "due_date": fake.date_between(start_date='today', end_date='+30d').isoformat(),
                "customer": {
                    "name": fake.company(),
                    "email": fake.email(),
                    "address": fake.address()
                },
                "line_items": line_items,
                "subtotal": subtotal,
                "tax": tax,
                "total": round(subtotal + tax, 2),
                "currency": "USD",
                "status": random.choice(["pending", "paid", "overdue"])
            }
        
        elif schema_type == "transaction":
            return {
                "id": fake.uuid4(),
                "amount": round(random.uniform(1.0, 10000.0), 2),
                "timestamp": datetime.utcnow().isoformat(),
                "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
                "status": random.choice(["pending", "completed", "failed"]),
                "merchant": fake.company(),
                "customer_id": fake.uuid4(),
                "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"])
            }
        
        else:  # user_event
            return {
                "user_id": fake.uuid4(),
                "event_type": random.choice(["page_view", "button_click", "form_submit", "purchase"]),
                "timestamp": datetime.utcnow().isoformat(),
                "properties": {
                    "page_url": fake.url(),
                    "user_agent": fake.user_agent(),
                    "session_id": fake.uuid4(),
                    "referrer": fake.url() if random.random() > 0.5 else None
                }
            }
    
    def generate_sample_pdf_content(self, doc_type: str = "invoice") -> str:
        """Generate sample PDF text content."""
        if doc_type == "invoice":
            line_items = []
            for i in range(random.randint(2, 6)):
                quantity = random.randint(1, 10)
                unit_price = round(random.uniform(50.0, 500.0), 2)
                total = round(quantity * unit_price, 2)
                line_items.append(f"{i+1}. {fake.catch_phrase()} - Qty: {quantity} @ ${unit_price:.2f} = ${total:.2f}")
            
            subtotal = sum(float(line.split('$')[-1]) for line in line_items)
            tax = round(subtotal * 0.08, 2)
            total = round(subtotal + tax, 2)
            
            return f"""
INVOICE

Invoice Number: INV-{fake.year()}-{fake.random_int(min=1000, max=9999)}
Date: {fake.date_between(start_date='-30d', end_date='today').strftime('%B %d, %Y')}
Due Date: {fake.date_between(start_date='today', end_date='+30d').strftime('%B %d, %Y')}

Bill To:
{fake.company()}
{fake.name()}
{fake.address()}
{fake.email()}

Line Items:
{chr(10).join(line_items)}

Subtotal: ${subtotal:.2f}
Tax (8%): ${tax:.2f}
Total Amount Due: ${total:.2f}

Payment Terms: Net 30 days
Thank you for your business!
"""
        
        elif doc_type == "contract":
            return f"""
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into on {fake.date_between(start_date='-30d', end_date='today').strftime('%B %d, %Y')} 
between {fake.company()} ("Company") and {fake.company()} ("Client").

WHEREAS, Company provides professional consulting services;
WHEREAS, Client desires to engage Company for such services;

NOW, THEREFORE, the parties hereby agree as follows:

1. SERVICES
Company shall provide consulting services as described in Exhibit A.

2. TERM
This Agreement shall commence on {fake.date_between(start_date='today', end_date='+30d').strftime('%B %d, %Y')} 
and continue for a period of {random.randint(6, 24)} months.

3. COMPENSATION
Client shall pay Company ${random.randint(5000, 50000):,} per month for services rendered.

4. CONFIDENTIALITY
Both parties agree to maintain confidentiality of proprietary information.

IN WITNESS WHEREOF, the parties have executed this Agreement.

Company: {fake.company()}
By: {fake.name()}, CEO

Client: {fake.company()}
By: {fake.name()}, Director
"""
        
        elif doc_type == "policy":
            compliance_type = random.choice(list(self.compliance_keywords.keys()))
            keywords = self.compliance_keywords[compliance_type]
            
            return f"""
{compliance_type} COMPLIANCE POLICY

Policy Number: POL-{fake.year()}-{fake.random_int(min=100, max=999)}
Effective Date: {fake.date_between(start_date='-365d', end_date='today').strftime('%B %d, %Y')}
Last Revised: {fake.date_between(start_date='-90d', end_date='today').strftime('%B %d, %Y')}

1. PURPOSE
This policy establishes guidelines for {compliance_type} compliance within our organization.

2. SCOPE
This policy applies to all employees, contractors, and third parties who handle {random.choice(keywords)}.

3. REQUIREMENTS
- All {random.choice(keywords)} must be protected according to {compliance_type} standards
- Regular audits must be conducted to ensure compliance
- Violations must be reported immediately to the compliance team
- Training on {compliance_type} requirements is mandatory for all staff

4. VIOLATIONS
Failure to comply with this policy may result in disciplinary action, including termination.

5. CONTACT
For questions regarding this policy, contact the Compliance Officer at compliance@{fake.domain_name()}.

Approved by: {fake.name()}, Chief Compliance Officer
Date: {fake.date_between(start_date='-30d', end_date='today').strftime('%B %d, %Y')}
"""
        
        else:  # report
            return f"""
QUARTERLY BUSINESS REPORT

Report Period: Q{random.randint(1, 4)} {fake.year()}
Prepared by: {fake.name()}, Business Analyst
Date: {fake.date_between(start_date='-30d', end_date='today').strftime('%B %d, %Y')}

EXECUTIVE SUMMARY
This report provides an analysis of business performance for the quarter ending {fake.date().strftime('%B %d, %Y')}.

KEY FINDINGS
- Revenue increased by {random.randint(5, 25)}% compared to previous quarter
- Customer satisfaction scores improved to {random.randint(85, 95)}%
- Operating costs decreased by {random.randint(2, 10)}%

RECOMMENDATIONS
1. Continue investment in customer service improvements
2. Expand marketing efforts in high-performing regions
3. Optimize operational processes to reduce costs further

FINANCIAL HIGHLIGHTS
Total Revenue: ${random.randint(100000, 1000000):,}
Net Profit: ${random.randint(10000, 100000):,}
Customer Acquisition Cost: ${random.randint(50, 200)}

CONCLUSION
The quarter showed strong performance across all key metrics. We recommend maintaining current strategies while exploring new growth opportunities.

For detailed analysis, see appendices A-C.
"""
    
    def generate_anomalous_json(self) -> Dict[str, Any]:
        """Generate JSON with intentional anomalies for testing."""
        base_data = self.generate_sample_json("webhook")
        
        # Introduce various anomalies
        anomaly_type = random.choice([
            "missing_required_field",
            "wrong_data_type", 
            "suspicious_amount",
            "malicious_content",
            "unusual_timestamp"
        ])
        
        if anomaly_type == "missing_required_field":
            # Remove a required field
            if "data" in base_data:
                base_data["data"].pop("user_id", None)
        
        elif anomaly_type == "wrong_data_type":
            # Change data type
            base_data["data"]["amount"] = "not_a_number"
        
        elif anomaly_type == "suspicious_amount":
            # Unusually high amount
            base_data["data"]["amount"] = 999999.99
        
        elif anomaly_type == "malicious_content":
            # Add potentially malicious content
            base_data["data"]["description"] = "<script>alert('xss')</script>"
            base_data["data"]["sql_injection"] = "'; DROP TABLE users; --"
        
        elif anomaly_type == "unusual_timestamp":
            # Future timestamp
            future_date = datetime.utcnow() + timedelta(days=365)
            base_data["timestamp"] = future_date.isoformat() + "Z"
        
        return base_data
    
    def generate_test_suite(self) -> Dict[str, List[Any]]:
        """Generate a complete test suite with various samples."""
        return {
            "emails": {
                "complaint": [self.generate_sample_email("complaint") for _ in range(3)],
                "rfq": [self.generate_sample_email("rfq") for _ in range(3)],
                "invoice": [self.generate_sample_email("invoice") for _ in range(3)]
            },
            "json": {
                "webhook": [self.generate_sample_json("webhook") for _ in range(5)],
                "invoice": [self.generate_sample_json("invoice") for _ in range(3)],
                "transaction": [self.generate_sample_json("transaction") for _ in range(5)],
                "anomalous": [self.generate_anomalous_json() for _ in range(3)]
            },
            "pdf_content": {
                "invoice": [self.generate_sample_pdf_content("invoice") for _ in range(3)],
                "contract": [self.generate_sample_pdf_content("contract") for _ in range(2)],
                "policy": [self.generate_sample_pdf_content("policy") for _ in range(2)],
                "report": [self.generate_sample_pdf_content("report") for _ in range(2)]
            }
        }


if __name__ == "__main__":
    generator = SampleDataGenerator()
    
    # Generate and save sample data
    test_suite = generator.generate_test_suite()
    
    with open("sample_data.json", "w") as f:
        json.dump(test_suite, f, indent=2, default=str)
    
    print("Sample data generated and saved to sample_data.json")
    
    # Print some examples
    print("\n=== Sample Email ===")
    print(generator.generate_sample_email("complaint"))
    
    print("\n=== Sample JSON ===")
    print(json.dumps(generator.generate_sample_json("webhook"), indent=2))
    
    print("\n=== Sample PDF Content ===")
    print(generator.generate_sample_pdf_content("invoice"))
