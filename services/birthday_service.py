from datetime import date, timedelta

def format_birthday(month: int, day: int) -> str:

    birthday = date(
        2000,
        month,
        day
    )

    return birthday.strftime("%B %d")

def get_days_until_birthday(
    month: int,
    day: int
) -> int:

    today = date.today()

    try:
        birthday = date(
            today.year,
            month,
            day
        )

    except ValueError:
        # February 29 on a non-leap year.
        birthday = date(
            today.year,
            2,
            28
        )

    if birthday < today:

        birthday = birthday.replace(
            year=today.year + 1
        )

        try:
            birthday = birthday.replace(
                month=month,
                day=day
            )

        except ValueError:
            birthday = date(
                today.year + 1,
                2,
                28
            )

    return (
        birthday - today
    ).days

def is_birthday_today(
    month: int,
    day: int
) -> bool:

    today = date.today()

    if (
        month == 2
        and day == 29
    ):

        if (
            today.month == 2
            and today.day == 28
        ):

            return True

    return (
        today.month == month
        and today.day == day
    )

def is_birthday_tomorrow(
    month: int,
    day: int
) -> bool:

    tomorrow = date.today() + timedelta(
        days=1
    )

    if (
        month == 2
        and day == 29
    ):

        return (
            tomorrow.month == 2
            and tomorrow.day == 28
        )

    return (
        tomorrow.month == month
        and tomorrow.day == day
    )

def is_birthday_in_seven_days(
    month: int,
    day: int
) -> bool:

    target = date.today() + timedelta(
        days=7
    )

    if (
        month == 2
        and day == 29
    ):

        return (
            target.month == 2
            and target.day == 28
        )

    return (
        target.month == month
        and target.day == day
    )