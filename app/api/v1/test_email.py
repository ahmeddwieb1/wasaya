from app.utils.scheduling import calculate_first_checkin

result = calculate_first_checkin(
    checkin_time="23:44",
    timezone_name="Africa/Cairo",
)

print(result)
print(result.isoformat())