# Tour Management: Per-Person Cost Calculator

This project is a group tour per-person cost calculator. It allows tour operators to add, edit, and manage tours with various pricing rules such as pricing based on based on group size, and taking into account fixed costs per person.

Per-person pricing can then more easily be calculated and presented back to customers wanting a quotation, whilst adjusting to the tour operators margins which change depending on the number of people attending.

Screenshot:
![Tour management system UI showing the basic but functional 'add tour' screen where tour operators can define pricing rules based on group size and also fixed per-person cost](./static/screenshot.png)

## Table of Contents

- Features
- Installation
- Usage
- Project Structure
- Contributing

## Features

- Add new tours with customisable pricing rules
- Manage fixed costs per person and price per person based on group size
- Simulate the costs of different group sizes with various fixed costs, taking into account group sizes
- Edit existing tours
- Simple file based storage- no complex database required

### Simulate the costs of different group sizes with various fixed costs, taking into account group sizes

![Simulate the costs of different group sizes](./static/screenshot-simulate-pricing.png)

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/tour-management-system.git
    cd tour-management-system
    ```

2. Create and activate a virtual environment:

    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the Flask application:

    ```sh
    flask run
    ```

2. Open your web browser and navigate to `http://127.0.0.1:5000` to access the Tour Management System.

## Project Structure

```shell
tour-management-system/
├── app.py
├── requirements.txt
├── state/
├── templates/
│   ├── admin.html
│   ├── edit_tour.html
│   ├── layout.html
│   ├── list-tours.html
│   └── macros/
│       ├── fixed_person_cost_form_controls_template.html
│       └── group_size_price_per_person_form_controls_template.html
```

## Endpoints

### `/api/calculate_cost_per_person` (`POST`)

Returns the full costings of the given tour. See [Data Model](#data-model).

### `/api/tour_per_person_price/<tour_code>/<int:number_of_people> (`GET`)

Returns the costs for a given `tour_code` and `number_of_people`.

E.g `curl http://127.0.0.1:5000/api/tour_per_person_price/LDNPUB2025/1`

## Data model

```python
tour = {
    "name": "London",
    "tour_code": "LDNPUB2025",
    "pricing_rules": {
        "max_people": 10,
        "min_people": 1,
        "fix_costs_per_person": [
            {"amount": 10, "name": "zoo_entrance"},
            {"amount": 5, "name": "snack"},
        ],
        "price_per_person_based_on_size_of_group": [
            {"min": 1, "max": 1, "price_per_person": 100},
            {"min": 2, "max": 5, "price_per_person": 80},
            {"min": 6, "max": 10, "price_per_person": 80},
        ],
    },
    "cost_per_person": "calculate_cost_per_person",
}
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.
