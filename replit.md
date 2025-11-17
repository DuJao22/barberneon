# Sistema de Gestão para Barbearia

## Overview
This project is a comprehensive management system for a barbershop, built with Python/Flask and SQLite3. It features a mobile-first design with a black and neon blue theme, inspired by delivery applications. The system aims to streamline barbershop operations, enhance customer experience through online services, and provide administrators with robust tools for managing products, services, appointments, and finances. The business vision is to offer a modern, efficient, and user-friendly platform for barbershop management, with market potential in digitizing small to medium-sized service businesses.

## User Preferences
I prefer iterative development with clear, concise explanations for each step. Please ask for confirmation before implementing major changes or architectural shifts. I like clean, readable code with a focus on maintainability and best practices. Ensure all new features are thoroughly tested and documented.

## System Architecture

### UI/UX Decisions
The system features a responsive, mobile-first design. The primary color scheme is black (#000000) for backgrounds, neon blue (#00E5FF) for highlights and interactive elements, white (#FFFFFF) for main text, light gray (#E0E0E0) for secondary text, and dark gray (#1a1a1a) for cards and containers. Text on light backgrounds uses #333333 for improved legibility. Navigation includes a fixed bottom bar (Catalog, Cart, History) and a sidebar for quick access. Category cards are square with rounded borders.

### Technical Implementations
- **Customer Interface**: Includes a home page with search and open/closed status, categorized service/product catalog, floating cart with badge, contact page, simplified client authentication (name + unique phone), online appointment system, and a checkout process.
- **Admin Panel**: Features a secure login (email/password), comprehensive management for services, products, barbers (with configurable commission types: percentage or fixed), appointments, financial dashboard, inventory control, virtual queue, and full order management (view, filter, confirm payment, cancel with stock return). A complete configuration system allows customization of barbershop details, operating hours, contact info, social media, and integration options like Mercado Pago.
- **Authentication**: Dual login system with separate paths for clients (name + unique phone, case-sensitive) and administrators (email + password). Login is mandatory for appointments and purchases. Admin credentials are `admin@barbearia.com` / `admin123`.
- **Security**: Measures include session secret management (auto-generated if not set), SQL injection protection via parameterization, comprehensive input validation, session fixation protection, no open redirect vulnerabilities, stock verification before sales, error handling with transaction rollbacks, user input sanitization, encrypted passwords (bcrypt), unique email constraint, and minimum password length.
- **CRUD Operations**: The admin panel supports full CRUD operations for products, services, and categories via API routes (`/admin/api/produtos`, `/admin/api/servicos`, `/admin/api/categorias`) with modal forms and JavaScript for interactive management.
- **Real-time Notifications**: Implemented for new appointments on the admin dashboard using a polling mechanism (every 10 seconds) to `/api/admin/check-novos-agendamentos`. When a client books an appointment, the admin receives an instant notification via both on-screen toast and browser native notification (if permitted). System tracks processed appointment IDs to prevent duplicates and auto-reloads the dashboard after 5 seconds to display new bookings.

### Feature Specifications
- **Configurable Barber Commissions**: Barbers can have commissions defined as a percentage (0-100%) or a fixed amount (>= 0), with automatic validation.
- **Order Management**: Allows viewing, filtering by status (Pending, Paid, Canceled), manual payment confirmation, and cancellation with automatic stock return.
- **System Settings**: Admin can customize barbershop name, logo/emoji, operating hours, open/closed status, contact information, address, social media links, description, average service time, and Mercado Pago activation.
- **Image System**: Products support images with fallback to emojis, displayed responsively.
- **Appointment Visualization**: Admin dashboard shows future appointments in interactive cards, with optional date filters and daily statistics.
- **Seamless Authentication Flow**: When unauthenticated users attempt to book appointments or make purchases, they are prompted to register or login via a friendly dialog. After authentication, users are automatically redirected back to complete their action with all data preserved (cart items, appointment details). The system saves pending appointment data in session and restores it post-login via `/obter-agendamento-pendente` endpoint, ensuring zero data loss.

### System Design Choices
- **Backend**: Python 3.x, Flask.
- **Database**: Pure SQLite3 (no ORM like SQLAlchemy).
- **Frontend**: HTML5, pure CSS3, Vanilla JavaScript.
- **Deployment**: Optimized for Render with Gunicorn for serving.

## External Dependencies
- **Python Libraries**: Listed in `requirements.txt` (Flask, Gunicorn, etc.).
- **Database**: SQLite3.
- **Deployment Platform**: Render.
- **Payment Gateway (Future Integration)**: Mercado Pago (requires configuration of secrets).
- **Browser APIs**: Notification API for real-time alerts.
```