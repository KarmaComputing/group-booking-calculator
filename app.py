from flask import Flask, render_template, flash, request
import secrets

"""

# Tours
- Each member *might* have a set cost
- You can't charge the same for 1 person as a group of 10
- Set cost example (e.g every partitipent gets entry to an
  attraction)
"""

tour = {
    "name": "London",
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


def calculate_cost_per_person(tour, number_of_people):
    total_cost = 0
    fixed_costs = 0
    # Honour the max/min people allowed on a tour
    assert number_of_people <= tour["pricing_rules"]["max_people"]
    assert number_of_people >= tour["pricing_rules"]["min_people"]

    # Calculate the fixed costs
    for fixed_cost in tour["pricing_rules"]["fix_costs_per_person"]:
        fixed_costs += fixed_cost["amount"]
        print(
            f"Adding fixed_cost {fixed_cost['name']}: £{fixed_cost['amount']}"
        )  # noqa: E501

    print(f"Total fixed costs for {number_of_people}: {fixed_costs}")

    # fixed_costs x number_of_people
    fixed_costs = fixed_costs * number_of_people
    # Calculate total_cost
    total_cost = fixed_costs
    print(f"Running cost is at: {total_cost}")

    # Find the matching group_size_person_price_rule
    for group_size_person_price_rule in tour["pricing_rules"][
        "price_per_person_based_on_size_of_group"
    ]:
        if (
            number_of_people >= group_size_person_price_rule["min"]
            and number_of_people <= group_size_person_price_rule["max"]
        ):
            print(f"Found the rule: {group_size_person_price_rule}")
            price_per_person = group_size_person_price_rule["price_per_person"]

    # Apply cost per-person based on group size
    print("Applying per-person cost")
    total_cost = total_cost + (price_per_person * number_of_people)
    print(f"Running cost is at: {total_cost}")

    print(f"Total cost is: {total_cost}")


app = Flask(__name__)
app.secret_key = secrets.token_hex()


@app.route("/")
def index():
    return render_template("admin.html")


@app.route("/api/tour", methods=["POST"])
def add_tour():
    # Get tour name
    tour_name = request.form.get("tour_name")
    # Get fixed costs per person
    for fixed_per_person_cost_name in request.form.getlist(
        "fixed_per_person_cost_name"
    ):
        print(fixed_per_person_cost_name)
    for fixed_per_person_cost_amount in request.form.getlist(
        "fixed_per_person_cost_amount"
    ):
        print(fixed_per_person_cost_amount)
    flash(f"Tour added: {tour_name}")
    return render_template("admin.html")
