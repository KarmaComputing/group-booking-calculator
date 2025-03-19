from flask import (
    Flask,
    render_template,
    flash,
    request,
    redirect,
    url_for,
    jsonify,
    after_this_request,
    make_response,
    current_app,
)  # noqa: E501
import secrets
import json
import pickle
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(verbose=True)  # take environment variables from .env.

STATE_DIR = os.getenv("BOOKING_STATE_DIR", "./state/")
COMPANY_NAME = os.getenv("COMPANY_NAME", "")
COMPANY_PHONE_NUMBER = os.getenv("COMPANY_PHONE_NUMBER")
PACKAGE_BASE_URL = os.getenv("PACKAGE_BASE_URL", "")
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://127.0.0.1:5000")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = os.getenv("SMTP_PORT", "465")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_DEFAULT_FROM_ADDR = os.getenv("SMTP_DEFAULT_FROM_ADDR")
COMPANY_WEB_ADDRESS = os.getenv("COMPANY_WEB_ADDRESS")

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

booking = {
    "tour_code": "LDNPUB2025",
    "number_of_people": 10,
    "quoted_price_per_person": 10,
    "name": "Fred",
    "email": "fred@example.com",
    "wechat_id": "abc123",
    "phone": "+4401234567890",
    "desired_tour_start_date": "yyy/mm/dd",
    "alternative_tour_start_time": "00:00",
    "alternative_tour_pickup_point": "Pizza Planet",
    "additional_transport_arrangement_requested": "Train",
    "preferred_payment_method": "paypal",
    "additional_comments": "Test",
}

"""
TODO: add to wordpress html event listener for order button

Array.from(document.getElementsByTagName("input")).forEach(function(input) {
 if (input.value == "Submit Your Order") {
     console.log(`Found it ${input}`);
     input.addEventListener("click", function(e) {
     alert("you clicked it!");
     });
 }
});

"""


def get_tours() -> dict:
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

    return tours


def calculate_cost_per_person(tour: dict, number_of_people: int) -> dict:
    total_cost = 0
    fixed_costs = 0
    number_of_people = int(number_of_people)

    # Calculate the fixed costs
    for fixed_cost in tour["pricing_rules"]["fix_costs_per_person"]:
        fixed_costs += int(fixed_cost["amount"])
        print(
            f"Adding fixed_cost {fixed_cost['name']}: £{fixed_cost['amount']}"
        )  # noqa: E501

    print(f"Total fixed costs for {number_of_people}: {fixed_costs}")

    # fixed_costs x number_of_people
    total_fixed_costs = fixed_costs * number_of_people
    # Calculate total_cost
    total_cost = total_fixed_costs
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

    resp = {
        "total_cost": total_cost,
        "total_fixed_costs": total_fixed_costs,
        "price_per_person": price_per_person,
    }

    return resp


def get_tour_by_tour_code(tour_code, get_index=False):
    """
    Return tour object from tours by tour_code or
    it's tour index if get_index is True
    """
    tours = get_tours()
    for index, tour in enumerate(tours):
        if tour["tour_code"] == tour_code:
            if get_index:
                return index
            else:
                return tour


app = Flask(__name__)
app.secret_key = secrets.token_hex()


# Load previously picked bookings if present
try:
    fp = open(f"{STATE_DIR}/bookings-pickle", mode="rb")
    bookings = pickle.load(fp)
    bookings = json.loads(bookings)
except (FileNotFoundError, EOFError):
    print(
        "pickle file is FileNotFoundError or "
        "EOFError. Writing empty bookings list"  # noqa: E501
    )  # noqa: E501
    with open(f"{STATE_DIR}/bookings-pickle", mode="wb") as fp:
        stub = json.dumps([])
        pickle.dump(stub, fp)
    fp = open("bookings-pickle", mode="rb")
    # Load newly created empty bookings object
    bookings = pickle.load(fp)
    bookings = json.loads(bookings)
except Exception as e:
    print(f"Error pickle {e}")


def save_tours_to_pickle_file(tours):
    # TODO assure structure
    with open(f"{STATE_DIR}/tours-pickle", mode="wb") as fp:
        pickle.dump(json.dumps(tours), fp)


def save_bookings_to_pickle_file(bookings):
    # TODO assure structure
    with open(f"{STATE_DIR}/bookings-pickle", mode="wb") as fp:
        pickle.dump(json.dumps(bookings), fp)


@app.after_request
def cors(response):
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", CORS_ORIGIN)  # noqa: E501
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type"
        )  # noqa: E501
        return response
    elif request.method == "POST":
        response.headers.add("Access-Control-Allow-Origin", CORS_ORIGIN)  # noqa: E501

    # Otherwise continue as normal
    return response


@app.context_processor
def additional_utilities():
    def get_tour_total_price(tour_code: str, number_of_people: int) -> int:
        tour = get_tour_by_tour_code(tour_code)
        if tour is None:
            return f"unknown tour: {tour_code}"
        return calculate_cost_per_person(tour, number_of_people)["total_cost"]

    def get_tour_per_person_price(
        tour_code: str, number_of_people: int
    ) -> int:  # noqa: E501
        tour = get_tour_by_tour_code(tour_code)
        if tour is None:
            return f"unknown tour: {tour_code}"
        return calculate_cost_per_person(tour, number_of_people)[
            "price_per_person"
        ]  # noqa: E501

    return dict(
        get_tour_total_price=get_tour_total_price,
        get_tour_per_person_price=get_tour_per_person_price,
    )


@app.template_filter("tsToHumanDateTime")
def tsToHumanDateTime(timestamp):
    try:
        humanDateTime = datetime.fromtimestamp(timestamp).strftime(
            "%Y/%m/%d %H:%M"
        )  # noqa: E501
    except Exception as e:
        print(f"Error parsing timestamp: {e}")
        humanDateTime = "Unknown"
    return humanDateTime


@app.route("/")
def index():
    return render_template("admin.html")


@app.route("/booking", methods=["GET"])
def list_bookings():
    return render_template(
        "list-bookings.html",
        bookings=bookings,
        PACKAGE_BASE_URL=PACKAGE_BASE_URL,  # noqa: E501
    )


@app.route("/booking", methods=["POST"])
def store_booking():
    booking = request.get_json()
    print(f"Echo'ing back the booking: {booking}")
    save_bookings_to_pickle_file(bookings)
    newBooking = {
        "created_at_ts": datetime.now(tz=timezone.utc).timestamp(),
        "tour_code": booking.get("tour_code"),
        "number_of_people": booking.get("number_of_people"),
        "name": booking.get("name"),
        "email": booking.get("email"),
        "wechat_id": booking.get("wechat_id"),
        "phone": booking.get("phone"),
        "desired_tour_start_date": booking.get("desired_tour_start_date"),
        "alternative_tour_start_time": booking.get(
            "alternative_tour_start_time"
        ),  # noqa: E501
        "alternative_tour_pickup_point": booking.get(
            "alternative_tour_pickup_point"
        ),  # noqa: E501
        "additional_transport_arrangement_requested": booking.get(
            "additional_transport_arrangement_requested"
        ),
        "preferred_payment_method": booking.get("preferred_payment_method"),
        "additional_comments": booking.get("additional_comments"),
    }
    bookings.append(newBooking)
    save_bookings_to_pickle_file(bookings)
    return booking


@app.route("/email/booking-quote/<int:booking_index>")
def resend_booking_quote(booking_index):
    num_bookings = len(bookings)
    inverted_index = num_bookings - booking_index
    booking = bookings[inverted_index]
    send_booking_quote(booking["email"], booking)
    flash("Booking quote re-sent")
    return redirect(url_for("list_bookings"))


def send_booking_quote(
    to_addr,
    booking,
    from_addr=SMTP_DEFAULT_FROM_ADDR,
):  # noqa: E501
    import smtplib
    from email.message import EmailMessage
    from email.utils import make_msgid
    from jinja2 import Template
    from pathlib import Path

    tour = get_tour_by_tour_code(booking["tour_code"])
    costs = calculate_cost_per_person(tour, booking["number_of_people"])

    TOUR_NAME = tour.get("name")
    subject = f"{COMPANY_NAME} - {TOUR_NAME}"
    NAME = booking.get("name")
    PRICE_PER_PERSON = costs.get("price_per_person")
    TOTAL_COST = costs.get("total_cost")
    PERSON_EMAIL = booking.get("email")
    WECHAT_ID = booking.get("wechat_id")
    PERSON_PHONE = booking.get("phone")
    DESIRED_TOUR_START_DATE = booking.get("desired_tour_start_date")
    PREFERRED_PAYMENT_METHOD = booking.get("preferred_payment_method")
    ADDITIONAL_COMMENTS = booking.get("additional_comments")
    NUMBER_OF_PEOPLE = booking.get("number_of_people")

    plainTextbody = (
        f"Hi {NAME}!\n"
        "Please find a review of your tour request below. We will check guide "
        "availability for your chosen tour and get back to you as "
        "soon as we can "
        "to confirm availability.\n\n"
        "Please note, this is not tour confirmation, and tours "
        "are not confirmed "
        "until you receive a confirmation email from us.\n\n"
        "If you are requesting a tour less than 36 hours "
        "ahead of the tour start "
        "date, or for any urgent enquiries, you are welcome to contact us at "
        f"{SMTP_DEFAULT_FROM_ADDR}.\n\n"
        "Hoping we can give you a truly British experience!\n\n"
        "Cheers!"
    )

    # html Template booking
    template = str(
        Path(
            f"{current_app.root_path}/templates/emails/booking-enquiry-confirmation.html"  # noqa: E501
        )  # noqa: E501
    )
    fp = open(template)
    template = fp.read()
    fp.close()

    jinja_template = Template(template)

    html = jinja_template.render(
        COMPANY_NAME=COMPANY_NAME,
        COMPANY_PHONE_NUMBER=COMPANY_PHONE_NUMBER,
        TOUR_NAME=TOUR_NAME,
        NAME=NAME,
        PRICE_PER_PERSON=PRICE_PER_PERSON,
        PERSON_EMAIL=PERSON_EMAIL,
        WECHAT_ID=WECHAT_ID,
        PERSON_PHONE=PERSON_PHONE,
        DESIRED_TOUR_START_DATE=DESIRED_TOUR_START_DATE,
        PREFERRED_PAYMENT_METHOD=PREFERRED_PAYMENT_METHOD,
        ADDITIONAL_COMMENTS=ADDITIONAL_COMMENTS,
        NUMBER_OF_PEOPLE=NUMBER_OF_PEOPLE,
        TOTAL_COST=TOTAL_COST,
        COMPANY_WEB_ADDRESS=COMPANY_WEB_ADDRESS,
        SMTP_DEFAULT_FROM_ADDR=SMTP_DEFAULT_FROM_ADDR,
    )

    msg = EmailMessage()
    msg.set_content(plainTextbody)  # PlainText body
    msg.add_alternative(html, subtype="html")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.add_header("Message-ID", make_msgid())

    s = smtplib.SMTP_SSL(host=SMTP_HOST, port=SMTP_PORT)
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    s.set_debuglevel(1)
    s.send_message(msg)


@app.route("/tours")
def list_tours():
    tours = get_tours()
    return render_template("list-tours.html", tours=tours)


@app.route("/tour/edit/<tour_code>", methods=["GET", "POST"])
def edit_tour(tour_code):
    tours = get_tours()
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


@app.route(
    "/api/tour_per_person_price/<tour_code>/<int:number_of_people>",
    methods=["GET"],  # noqa: E501
)  # noqa: E501
def api_get_tour_per_person_price_by_tour_code(tour_code, number_of_people):
    @after_this_request
    def add_header(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    tour = get_tour_by_tour_code(tour_code)

    costs = calculate_cost_per_person(tour, number_of_people)
    # Remove total_fixed_costs from response
    costs.pop("total_fixed_costs", None)
    return jsonify(costs)


@app.route("/api/tour", methods=["POST"])
def add_tour():
    tours = get_tours()
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
