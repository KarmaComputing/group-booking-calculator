from flask import (
    Flask,
    render_template,
    flash,
    request,
    redirect,
    url_for,
    jsonify,
)  # noqa: E501
import secrets
import json
import pickle
import os

STATE_DIR = os.getenv("BOOKING_STATE_DIR", "./state/")

"""

# Tours
- Each member *might* have a set cost
- You can't charge the same for 1 person as a group of 10
- Set cost example (e.g every participant gets entry to an
  attraction)
"""

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


def calculate_cost_per_person(tour: dict, number_of_people: int) -> dict:
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
        if number_of_people >= int(
            group_size_person_price_rule["min"]
        ) and number_of_people <= int(group_size_person_price_rule["max"]):
            print(f"Found the rule: {group_size_person_price_rule}")
            price_per_person = int(
                group_size_person_price_rule["price_per_person"]
            )  # noqa: E501

    # Apply cost per-person based on group size
    print("Applying per-person cost")
    total_cost = total_cost + (price_per_person * number_of_people)
    print(f"Running cost is at: {total_cost}")

    print(f"Total cost is: {total_cost}")

    resp = {"total_cost": total_cost, "price_per_person": price_per_person}

    return resp


def get_tour_by_tour_code(tour_code, get_index=False):
    """
    Return tour object from tours by tour_code or
    it's tour index if get_index is True
    """
    for index, tour in enumerate(tours):
        if tour["tour_code"] == tour_code:
            if get_index:
                return index
            else:
                return tour


app = Flask(__name__)
app.secret_key = secrets.token_hex()

# Load previously pickled tours if present
try:
    fp = open(f"{STATE_DIR}/tours-pickle", mode="rb")
    tours = pickle.load(fp)
    tours = json.loads(tours)
except (FileNotFoundError, EOFError):
    print(
        "pickle file is FileNotFoundError or "
        "EOFError. Writing empty tours list"  # noqa: E501
    )  # noqa: E501
    with open(f"{STATE_DIR}/tours-pickle", mode="wb") as fp:
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
    with open(f"{STATE_DIR}/tours-pickle", mode="wb") as fp:
        pickle.dump(json.dumps(tours), fp)


@app.route("/")
def index():
    return render_template("admin.html")


@app.route("/tours")
def list_tours():
    return render_template("list-tours.html", tours=tours)


@app.route("/tour/edit/<tour_code>", methods=["GET", "POST"])
def edit_tour(tour_code):
    tour = get_tour_by_tour_code(tour_code)
    original_tour_code = request.form.get("original_tour_code")

    if request.method == "GET":
        return render_template("edit_tour.html", tour=tour)
    elif request.method == "POST":
        print("Processing tour edit")
        # Get tour name
        tour_name = request.form.get("tour_name")
        tour_code = request.form.get("tour_code")
        min_people = request.form.get("min_people")
        max_people = request.form.get("max_people")

        print("Getting price_per_person_group_size_form_controls_count")
        price_per_person_group_size_form_controls_count = int(
            request.form["price_per_person_group_size_form_controls_count"]
        )
        price_per_person_based_on_size_of_group = []

        for index in range(
            0, price_per_person_group_size_form_controls_count
        ):  # noqa: E501
            min = int(request.form[f"min_people_group_size_price-{index}"])
            max = int(request.form[f"max_people_group_size_price-{index}"])
            price_per_person = int(
                request.form[f"group_size_price_per_person-{index}"]
            )  # noqa: E501

            price_per_person_based_on_size_of_group.append(
                {"min": min, "max": max, "price_per_person": price_per_person}
            )

            if price_per_person_group_size_form_controls_count == 1:
                print(
                    "Breaking out of loop price_per_person_group_size_"
                    "form_controls_count is {price_per_person_group_size_form_controls_count}"  # noqa: E501
                )
                break

        print(
            f"Built object price_per_person_based_on_size_of_group as: {price_per_person_based_on_size_of_group}"  # noqa: E501
        )

        print("Getting fixed_person_cost_form_controls_count")
        fixed_person_cost_form_controls_count = request.form[
            "fixed_person_cost_form_controls_count"
        ]  # noqa: E501

        fix_costs_per_person = []
        for fixed_per_person_cost_index in range(
            0, int(fixed_person_cost_form_controls_count)
        ):
            fixed_per_person_cost_name = request.form[
                f"fixed_per_person_cost_name-{fixed_per_person_cost_index}"
            ]
            fixed_per_person_cost_amount = request.form[
                f"fixed_per_person_cost_amount-{fixed_per_person_cost_index}"
            ]
            fix_costs_per_person.append(
                {
                    "name": fixed_per_person_cost_name,
                    "amount": fixed_per_person_cost_amount,
                }
            )

            if fixed_person_cost_form_controls_count == 1:
                print(
                    "Breaking out of loop fixed_person_cost_form_controls_count"  # noqa: E501
                    "form_controls_count is {fixed_person_cost_form_controls_count}"  # noqa: E501
                )
                break

        # Build and update tour object
        updated_tour = {
            "name": tour_name,
            "tour_code": tour_code,
            "pricing_rules": {
                "max_people": max_people,
                "min_people": min_people,
                "fix_costs_per_person": fix_costs_per_person,
                "price_per_person_based_on_size_of_group": price_per_person_based_on_size_of_group,  # noqa: E501
            },
            "cost_per_person": "calculate_cost_per_person",
        }

        original_tour_index = get_tour_by_tour_code(
            original_tour_code, get_index=True
        )  # noqa: E501
        tours[original_tour_index] = updated_tour
        save_tours_to_pickle_file(tours)
        flash(f'Tour "{tour_name}" updated')
    return redirect(url_for("list_tours"))


@app.route("/api/calculate_cost_per_person", methods=["POST"])
def api_calculate_cost_per_person():
    number_of_people = request.json.get("number_of_people")
    tour = request.json.get("tour")
    resp = calculate_cost_per_person(tour, number_of_people)
    return jsonify(resp)


@app.route("/api/tour", methods=["POST"])
def add_tour():
    # Get tour name
    tour_name = request.form.get("tour_name")
    tour_code = request.form.get("tour_code")
    min_people = request.form.get("min_people")
    max_people = request.form.get("max_people")

    # Get fixed costs per person
    fix_costs_per_person = []
    fixed_person_cost_form_controls_count = int(
        request.form["fixed_person_cost_form_controls_count"]
    )  # noqa: E501

    for index in range(0, fixed_person_cost_form_controls_count):
        fix_costs_per_person.append(
            {
                "name": request.form.get(
                    f"fixed_per_person_cost_name-{index}"
                ),  # noqa: E501
                "amount": request.form.get(
                    f"fixed_per_person_cost_amount-{index}"
                ),  # noqa: E501
            }
        )

    print(f"fix_costs_per_person are {fix_costs_per_person}")

    # Get prices per person group size ranges
    price_per_person_group_size_form_controls_count = int(
        request.form["price_per_person_group_size_form_controls_count"]
    )
    price_per_person_based_on_size_of_group = []
    for index in range(0, price_per_person_group_size_form_controls_count):
        price_per_person_based_on_size_of_group.append(
            {
                "min": request.form[f"min_people_group_size_price-{index}"],
                "max": request.form[f"max_people_group_size_price-{index}"],
                "price_per_person": request.form[
                    f"group_size_price_per_person-{index}"
                ],
            }
        )

    # Build valid tour object
    tour = {
        "name": tour_name,
        "tour_code": tour_code,
        "pricing_rules": {
            "max_people": int(max_people),
            "min_people": int(min_people),
            "fix_costs_per_person": fix_costs_per_person,
            "price_per_person_based_on_size_of_group": price_per_person_based_on_size_of_group,  # noqa: E501
        },
    }

    tours.append(tour)
    save_tours_to_pickle_file(tours)

    flash(f"Tour added: {tour_name}")
    return redirect(url_for("list_tours"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008)
