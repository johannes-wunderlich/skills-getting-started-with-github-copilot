from copy import deepcopy

import httpx
import pytest

import src.app as app_module

ORIGINAL_ACTIVITIES = deepcopy(app_module.activities)


def reset_activities():
    app_module.activities.clear()
    app_module.activities.update(deepcopy(ORIGINAL_ACTIVITIES))


@pytest.fixture
async def client():
    reset_activities()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_module.app),
        base_url="http://testserver"
    ) as async_client:
        yield async_client


@pytest.mark.anyio
async def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = await client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert expected_activity in data
    assert isinstance(data[expected_activity]["participants"], list)


@pytest.mark.anyio
async def test_signup_accepts_valid_mergington_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = await client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app_module.activities[activity_name]["participants"]


@pytest.mark.anyio
async def test_signup_rejects_invalid_email_domain(client):
    # Arrange
    activity_name = "Chess Club"
    email = "baduser@example.com"

    # Act
    response = await client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Email must be a valid @mergington.edu address"


@pytest.mark.anyio
async def test_signup_rejects_duplicate_signup(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = await client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


@pytest.mark.anyio
async def test_remove_participant_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = await client.delete(
        f"/activities/{activity_name}/participants?email={email}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


@pytest.mark.anyio
async def test_remove_participant_nonexistent_returns_404(client):
    # Arrange
    activity_name = "Chess Club"
    email = "absent@mergington.edu"

    # Act
    response = await client.delete(
        f"/activities/{activity_name}/participants?email={email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
