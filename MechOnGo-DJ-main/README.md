# MechOnGo - AutoCare Service Management System

A Django-based web application that connects **customers** with **mechanics** for vehicle service management.  
It provides dashboards for both roles, **OTP-based job verification**, booking, payments, and rating features.

---

## Screenshots

### Home
<img width="1693" height="4735" alt="image" src="https://github.com/user-attachments/assets/19068a5c-67e1-4426-a8fe-407c6a7cff6a" />

### Authentication
<img width="1829" height="963" alt="image" src="https://github.com/user-attachments/assets/1c3feb79-ba04-459e-bc8c-8f9dc9c77751" />

### Customer Dashboard
<img width="1693" height="1211" alt="image" src="https://github.com/user-attachments/assets/cf5676af-1cf7-4eb9-b08a-a499272e9edd" />

### Book Service
<img width="1693" height="2077" alt="image" src="https://github.com/user-attachments/assets/885a1e49-b1f3-4fe5-bedc-2977fc2f5973" />
   
### History
<img width="1693" height="2005" alt="image" src="https://github.com/user-attachments/assets/5c26e2d4-7c37-4930-acfc-6ec7e78170d2" />

# Summary of Bookings
<img width="1693" height="1185" alt="image" src="https://github.com/user-attachments/assets/06a1776f-99c4-48f2-951a-60890887f2e9" />

# Rating
<img width="1693" height="1440" alt="image" src="https://github.com/user-attachments/assets/bad1ce39-c0aa-459b-8977-131c010ee3c3" />

### Mechanic Dashboard
<img width="1693" height="1439" alt="image" src="https://github.com/user-attachments/assets/746832e8-86e3-495b-893c-01f307dd8ad0" />

### OTP Verification
The below screenshot is from Mechanic
<img width="1693" height="1001" alt="image" src="https://github.com/user-attachments/assets/afa91111-a8e0-488a-92dd-98097ba346a5" />

The below screenshot is from customer
<img width="1880" height="969" alt="image" src="https://github.com/user-attachments/assets/cc844352-98ca-4863-8334-5eaeea6ee689" />

---

## Features

### Authentication & Profiles
- Separate signup/login for **customers** and **mechanics**
- Profile management for both roles
- Secure authentication using Django’s built-in auth system

### Mechanic Features
- View & accept pending service requests
- Start and complete jobs with **OTP verification**
- Service calendar for active jobs
- Track completed jobs and ratings
- Manage mechanic profile

### Customer Features
- Book a vehicle service with date/time preferences
- Track service progress and job status
- View and pay invoices
- Manage payment methods
- Rate and review completed services
- View order history

### Job & Service Management
- Service request lifecycle: **Pending → Scheduled → In Progress → Completed**
- OTP-based verification for job start & completion
- Real-time job tracking
- Automatic invoice generation

### Payments
- Add and manage payment methods
- Pay invoices for completed jobs
- Track pending and completed payments

---

## Tech Stack

- **Backend**: Django, Django ORM
- **Frontend**: Django Templates, Bootstrap
- **Database**: SQLite (default), compatible with PostgreSQL/MySQL
- **Authentication**: Django Auth
- **Other**: Logging, Django Messages, AJAX for live updates

---

## Installation & Setup

1. **Clone the repository**
   ```bash
   https://github.com/ARIHARAN-KC/MechOnGo-DJ.git
   
2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt

4. **Run migrations**
   ```bash
   python manage.py migrate

5. **Create a superuser (for admin access)**
   ```bash
   python manage.py createsuperuser

6. **Run the development server**
   ```bash
   python manage.py runserver

7. **Open in browser**
   ```bash
   http://127.0.0.1:8000

---

**Future Enhancements**
   
   - Push notifications for job status updates
   
   - Live mechanic tracking with GPS
   
   - Email/SMS OTP delivery
   
   - Payment gateway integration (Stripe/PayPal)

---

**Contributing**

   - Fork this repository
   
   - Create a new branch (feature)
   
   - Commit your changes (git commit -m "Added feature name")
   
   - Push to your branch and create a Pull Request

---

**License**
   - This project is licensed under the MIT License – you are free to use, modify, and distribute.

---

**Author**

   - Ariharan K C
   - ariharankc@gmail.com.com
   - [LinkedIn](https://www.linkedin.com/in/ariharankc07/) | [GitHub](https://github.com/ARIHARAN-KC/) | [Portfolifo](https://ariharan-portfolifo.vercel.app/)
