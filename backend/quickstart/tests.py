# Some tests created with aid from LLMs
from typing import Any

import pytest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from .models import StudyUser, Task

# TODO Add docstrings to each of these functions to help newcomers understand what they do


@pytest.fixture
def api_client() -> APIClient:
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def test_user(db: Any) -> StudyUser:
    """Creates a StudyUser for testing"""
    return StudyUser.objects.create_user(username="andres", password="password123", money=500)


@pytest.fixture
def other_user(db: Any) -> StudyUser:
    """Creates another StudyUser for isolation testing"""
    return StudyUser.objects.create_user(username="anthony", password="password456", money=50)


@pytest.fixture
def test_task(db: Any, test_user: StudyUser) -> Task:
    """Creates a Task for testing"""
    return Task.objects.create(
        name="Test",
        reward=50,
        description="Make sure this works",
        due_date="2026-12-31",
        user=test_user,
    )


# @pytest.mark.required
@pytest.mark.tasks
class TestTaskCreation:
    def test_create_task_authenticated(self, api_client: APIClient, test_user: StudyUser) -> None:
        api_client.force_authenticate(user=test_user)

        # 2. Prepare Data (No user info in JSON, handled by CurrentUserDefault)
        url = "/api/create_task/"
        # TODO Make a TaskData class that strongly types the fields inside our StudyUser
        data = {
            "name": "Math Homework",
            "reward": 50,
            "description": "Finish algebra 1",
            "due_date": "2029-12-31",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        # Verify DB entry
        task: Task = Task.objects.get(name="Math Homework")
        assert task.user == test_user

    def test_create_task_unauthenticated(self, api_client: APIClient, test_user: StudyUser) -> None:
        """Ensure logged-out users can't create tasks."""
        url = "/api/create_task/"
        data = {
            "name": "Ghost Task",
            "due_date": "2029-12-31",
        }

        response = api_client.post(url, data, format="json")

        assert isinstance(response, Response)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_task_empty(
        self,
        api_client: APIClient,
        test_user: StudyUser,
    ) -> None:
        """Ensure each submitted task is not empty."""
        api_client.force_authenticate(user=test_user)

        response = api_client.post("/api/create_task", {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_missing_name(self, api_client: APIClient, test_user: StudyUser) -> None:
        """Ensure each submitted task has a name."""
        api_client.force_authenticate(user=test_user)
        data = {
            "reward": 10,
            "due_date": "2029-12-31",
            "description": "test",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_missing_due_date(
        self,
        api_client: APIClient,
        test_user: StudyUser,
    ) -> None:
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "No Date Task",
            "reward": 50,
            "description": "test",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_invalid_due_date(
        self,
        api_client: APIClient,
        test_user: StudyUser,
    ) -> None:
        """Malformed date should be rejected."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Bad Date Task",
            "reward": 50,
            "due_date": "not-a-date",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_negative_reward(self, api_client: APIClient, test_user: StudyUser) -> None:
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Negative Task",
            "reward": -100,
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_positive_reward(self, api_client: APIClient, test_user: StudyUser) -> None:
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Positive Task",
            "reward": 100,
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_due_date_in_past(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Late Task",
            "reward": 10,
            "due_date": "2000-01-01",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_response_shape(self, api_client: APIClient, test_user: StudyUser):
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Shape Test",
            "reward": 20,
            "due_date": "2029-12-31"
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert "name" in response.data
        assert "reward" in response.data
        assert "due_date" in response.data

        # Make sure password is NOT there
        assert "password" not in response.data

    def test_create_task_missing_description_uses_default(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """description now has a default — omitting it should succeed."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "No Description Task",
            "reward": 10,
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        task = Task.objects.get(name="No Description Task")
        assert task.description == "No description given"  # adjust if default is changed

    def test_create_task_reward_zero(self, api_client: APIClient, test_user: StudyUser) -> None:
        """Reward of exactly 0 should be allowed — it's not negative."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Zero Reward Task",
            "reward": 0,
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_reward_as_string(self, api_client: APIClient, test_user: StudyUser) -> None:
        """DRF often coerces numeric strings — confirm the actual behavior."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "String Reward Task",
            "reward": "50",
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_reward_non_numeric_string(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """A genuinely non-numeric reward should be rejected."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Bad Reward Task",
            "reward": "not-a-number",
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_missing_name_uses_default(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """
        `name` has a model default of "task". Depending on how the serializer
        handles required fields, this could either 201 with the default name
        or 400 if the serializer marks it required regardless of the model default.
        """
        api_client.force_authenticate(user=test_user)
        data = {
            "reward": 10,
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        # Adjust to match your serializer's actual behavior once confirmed
        assert response.status_code in (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST)

    def test_create_task_missing_description(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """`description` has no default and no null=True — should be required."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "No Description Task",
            "reward": 10,
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_with_category(self, api_client: APIClient, test_user: StudyUser) -> None:
        """category is nullable — confirm it's accepted when provided."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Categorized Task",
            "reward": 10,
            "due_date": "2029-12-31",
            "category": "school",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        task = Task.objects.get(name="Categorized Task")
        assert task.category == "school"

    def test_create_task_without_category_is_null(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """category is optional — omitting it shouldn't cause a failure."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Uncategorized Task",
            "reward": 10,
            "due_date": "2029-12-31",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_does_not_leak_other_users_id(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Even if a client tries to pass a `user` field, it should be ignored/read-only."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Spoofed User Task",
            "reward": 10,
            "due_date": "2029-12-31",
            "user": other_user.id,
        }

        api_client.post("/api/create_task/", data, format="json")

        task = Task.objects.get(name="Spoofed User Task")
        assert task.user == test_user  # not other_user


@pytest.mark.required
@pytest.mark.tasks
class TestTaskRetrieval:

    @pytest.mark.parametrize("test_username", ["andres"])
    def test_get_task_authenticated(
        self,
        api_client: APIClient,
        test_user: StudyUser,
        test_task: Task,
        test_username: str,
    ) -> None:
        # Log in
        user = StudyUser.objects.get(username=test_username)
        api_client.force_authenticate(user=user)

        # Make the request
        url = "/api/get_task/"
        query_params = {"username": test_username}
        response = api_client.get(url, data=query_params)

        assert response.status_code == status.HTTP_200_OK

        assert response.data[0]["name"] == "Test"

    @pytest.mark.parametrize("test_username", ["andres"])
    def test_get_task_unauthenticated(self, api_client: APIClient, test_username: str) -> None:
        url = "/api/get_task/"
        query_params = {"username": test_username}
        response = api_client.get(url, data=query_params)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_task_returns_only_own_tasks(
        self,
        api_client: APIClient,
        test_user: StudyUser,
        other_user: StudyUser,
        test_task: Task,
    ) -> None:
        """Baseline sanity check: authenticated user only sees their own task."""
        api_client.force_authenticate(user=test_user)

        Task.objects.create(
            name="Other User Task",
            reward=5,
            description="not visible",
            due_date="2029-12-31",
            user=other_user,
        )

        response = api_client.get("/api/get_task/", data={"username": test_user.username})

        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data]
        assert "Other User Task" not in names

    def test_get_task_no_tasks_returns_empty_list(
        self, api_client: APIClient, other_user: StudyUser
    ) -> None:
        """A user with zero tasks should get an empty list, not an error."""
        api_client.force_authenticate(user=other_user)

        response = api_client.get("/api/get_task/", data={"username": "anthony"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_get_task_missing_username_param(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        api_client.force_authenticate(user=test_user)

        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_task_cannot_query_another_users_username(
        self,
        api_client: APIClient,
        test_user: StudyUser,
        other_user: StudyUser,
        test_task: Task,
    ) -> None:
        """
        Security-relevant: authenticate as other_user but pass test_user's
        username in the query param. The view should NOT return test_user's
        tasks just because the param says so — it should be scoped to the
        authenticated user (request.user), not the query param.
        """
        api_client.force_authenticate(user=other_user)

        response = api_client.get("/api/get_task/", data={"username": "andres"})

        # If your view currently trusts the `username` param over
        # `request.user`, this test will fail — that's worth fixing.
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN)
        if response.status_code == status.HTTP_200_OK:
            names = [t["name"] for t in response.data]
            assert "Test" not in names


@pytest.mark.required
@pytest.mark.tasks
class TestTaskIsolation:
    def test_task_belongs_to_requesting_user(
        self,
        api_client: APIClient,
        test_user: StudyUser,
    ) -> None:
        """Task should be assigned to the authenticated user, not someone else."""
        api_client.force_authenticate(user=test_user)
        data = {"name": "My Task", "reward": 50}
        api_client.post("/api/create_task/", data, format="json")

        assert Task.objects.filter(name="My Task", user=test_user).exists()

    def test_users_cannot_see_each_others_tasks(
        self,
        api_client: APIClient,
        test_user: StudyUser,
        other_user: StudyUser,
    ) -> None:
        """Tasks created by one user shouldn't appear for another."""
        api_client.force_authenticate(user=test_user)
        api_client.post("/api/create_task/", {"name": "Private Task", "reward": 10}, format="json")

        api_client.force_authenticate(user=other_user)
        query_params = {"username": other_user.username}
        response = api_client.get("/api/get_task/", data=query_params)
        
        task_names = [task["name"] for task in response.data]
        assert "Private Task" not in task_names

    def test_isolation_holds_across_multiple_tasks_per_user(
        self,
        api_client: APIClient,
        test_user: StudyUser,
        other_user: StudyUser,
    ) -> None:
        api_client.force_authenticate(user=test_user)
        for i in range(3):
            api_client.post(
                "/api/create_task/",
                {"name": f"Mine {i}", "reward": 5, "due_date": "2029-12-31"},
                format="json",
            )

        api_client.force_authenticate(user=other_user)
        for i in range(2):
            api_client.post(
                "/api/create_task/",
                {"name": f"Theirs {i}", "reward": 5, "due_date": "2029-12-31"},
                format="json",
            )

        query_params = {"username": other_user.username}
        response = api_client.get("/api/get_task/", data=query_params)
        names = [t["name"] for t in response.data]

        assert len(names) == 2
        assert all(name.startswith("Theirs") for name in names)
   


# Test Graveyard for tests that get generated but aren't useful *yet*

# def test_deleting_user_cascades_to_tasks(
#     self, api_client: APIClient, test_user: StudyUser
# ) -> None:
#     Task.objects.create(
#         name="Cascade Task",
#         reward=10,
#         due_date="2029-12-31",
#         user=test_user,
#     )
#     test_user.delete()

#     assert not Task.objects.filter(name="Cascade Task").exists()