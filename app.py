from flask import Flask, render_template, flash, request, redirect, url_for, jsonify
import secrets
import json
import pickle

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

    # Calculate the fixed costs
    for fixed_cost in tour["pricing_rules"]["fix_costs_per_person"]:
        fixed_costs += int(fixed_cost["amount"])
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

# Load previously pickled tours if present
try:
    fp = open("tours-pickle", mode="rb")
    tours = pickle.load(fp)
    tours = json.loads(tours)
except (FileNotFoundError, EOFError):
    print("picke file is FileNotFoundError or EOFError. Writing empty tours list")
    with open("tours-pickle", mode="wb") as fp:
        stub = json.dumps([])
        pickle.dump(stub, fp)
    fp = open("tours-pickle", mode="rb")
    # Load newly created empty tours object
    tours = pickle.load(fp)
    tours = json.loads(tours)
except Exception as e:
    print(f"Error pickle {e}")


def save_tours_to_pickle_file(tours):
    # TODO assure structure
    with open("tours-pickle", mode="wb") as fp:
        pickle.dump(json.dumps(tours), fp)


@app.route("/")
def index():
    return render_template("admin.html")


@app.route("/tours")
def list_tours():
    return render_template("list-tours.html", tours=tours)


@app.route("/api/tour", methods=["POST"])
def add_tour():
    # Get tour name
    tour_name = request.form.get("tour_name")
    tour_code = request.form.get("tour_code")
    min_people = request.form.get("min_people")
    max_people = request.form.get("max_people")

    # Get fixed costs per person
    fixed_per_person_cost_names = request.form.getlist(
        "fixed_per_person_cost_name"
    )  # noqa: E501
    fixed_per_person_cost_amounts = request.form.getlist(
        "fixed_per_person_cost_amount"
    )  # noqa: E501

    fix_costs_per_person = dict(
        zip(fixed_per_person_cost_names, fixed_per_person_cost_amounts)
    )
    print(f"fix_costs_per_person are {fix_costs_per_person}")

    fix_costs_per_person = [
        {"name": fixed_pp_cost_name, "amount": fixed_pp_cost_amount}
        for fixed_pp_cost_name, fixed_pp_cost_amount in zip(
            fixed_per_person_cost_names, fixed_per_person_cost_amounts
        )
    ]

    # Get prices per person group size ranges
    min_people_group_size_prices = request.form.getlist(
        "min_people_group_size_price"
    )  # noqa: E501

    max_people_group_size_prices = request.form.getlist(
        "max_people_group_size_price"
    )  # noqa: E501

    group_size_price_per_persons = request.form.getlist(
        "group_size_price_per_person"
    )  # noqa: E501

    # Combind min/max/price_per_person into structure desired for calculation
    price_per_person_based_on_size_of_group = [
        {"min": int(min_p), "max": int(max_p), "price_per_person": int(price)}
        for min_p, max_p, price in zip(
            min_people_group_size_prices,
            max_people_group_size_prices,
            group_size_price_per_persons,
        )
    ]

    # Build valid tour object
    tour = {
        "name": tour_name,
        "pricing_rules": {
            "max_people": int(max_people),
            "min_people": int(min_people),
            "fix_costs_per_person": fix_costs_per_person,
            "price_per_person_based_on_size_of_group": price_per_person_based_on_size_of_group,
        },
    }

    tours.append(tour)
    save_tours_to_pickle_file(tours)

    flash(f"Tour added: {tour_name}")
    return redirect(url_for("list_tours"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008)
