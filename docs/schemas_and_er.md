# Relational Dataset Schemas & ER Diagram

This document details the relational entity schema architecture and Entity-Relationship (ER) diagram for the Enterprise Retail Sales Analytics Platform.

---

## 📐 Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    REGIONS ||--|{ STORES : "contains"
    REGIONS ||--|{ CUSTOMERS : "resides_in"
    CATEGORIES ||--|{ PRODUCTS : "classifies"
    CUSTOMERS ||--|{ ORDERS : "places"
    STORES ||--|{ ORDERS : "fulfills"
    PRODUCTS ||--|{ ORDERS : "contains"
    TIME_DIMENSION ||--|{ ORDERS : "occurred_on"
    PAYMENT_METHODS ||--|{ ORDERS : "paid_with"
    ORDERS ||--o| RETURNS : "generates"
    ORDERS ||--o| DISCOUNTS : "applies"
    ORDERS ||--|| SHIPPING : "dispatches"

    REGIONS {
        string region_id PK
        string region_name
        string country
        string manager_name
    }

    STORES {
        string store_id PK
        string store_name
        string region_id FK
        string store_type
        int sqft_area
    }

    CATEGORIES {
        string category_id PK
        string category_name
        string department
    }

    PRODUCTS {
        string product_id PK
        string product_name
        string category_id FK
        float cost_price
        float unit_price
        float popularity_score
        int stock_quantity
    }

    CUSTOMERS {
        string customer_id PK
        string name
        string email
        string segment
        string region_id FK
        date signup_date
        float churn_risk_score
    }

    TIME_DIMENSION {
        int date_key PK
        date full_date
        int year
        int quarter
        int month
        string month_name
        int week_of_year
        int day_of_week
        boolean is_weekend
        boolean is_holiday
    }

    PAYMENT_METHODS {
        string payment_method_id PK
        string method_name
    }

    ORDERS {
        string order_id PK
        string customer_id FK
        string product_id FK
        string store_id FK
        int date_key FK
        int quantity
        float unit_price
        float discount_amount
        float total_amount
        float cost_amount
        float profit_amount
        string payment_method_id FK
    }

    RETURNS {
        string return_id PK
        string order_id FK
        date return_date
        string return_reason
        float refund_amount
    }

    DISCOUNTS {
        string discount_id PK
        string order_id FK
        string promo_code
        float discount_percent
    }

    SHIPPING {
        string shipping_id PK
        string order_id FK
        string shipping_mode
        float shipping_cost
        string carrier
        boolean is_delayed
    }
```

---

## 📊 Data Dictionary & Relational Tables

### 1. `customers`
- **Primary Key**: `customer_id` (`CUST-000001` format)
- **Foreign Keys**: `region_id` -> `regions.region_id`
- **Attributes**: `name`, `email`, `segment` (Consumer, Corporate, Home Office), `signup_date`, `churn_risk_score` (Beta distribution $\alpha=2.0, \beta=5.0$).

### 2. `products`
- **Primary Key**: `product_id` (`PRD-01001` format)
- **Foreign Keys**: `category_id` -> `categories.category_id`
- **Attributes**: `product_name`, `cost_price`, `unit_price`, `popularity_score` (Pareto distribution $\alpha=1.16$), `stock_quantity`.

### 3. `orders` (Fact Table)
- **Primary Key**: `order_id` (`ORD-1000001` format)
- **Foreign Keys**:
  - `customer_id` -> `customers.customer_id`
  - `product_id` -> `products.product_id`
  - `store_id` -> `stores.store_id`
  - `date_key` -> `time_dimension.date_key`
  - `payment_method_id` -> `payment_methods.payment_method_id`
- **Calculated Line Metrics**:
  - $\text{total\_amount} = (\text{unit\_price} \times \text{quantity}) - \text{discount\_amount}$
  - $\text{cost\_amount} = \text{cost\_price} \times \text{quantity}$
  - $\text{profit\_amount} = \text{total\_amount} - \text{cost\_amount}$
