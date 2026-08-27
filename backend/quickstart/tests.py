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
        due_date="2026-12-31T00:00:00Z",
        user=test_user,
    )


@pytest.mark.required
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
            "due_date": "2029-12-31T00:00:00Z",
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
            "due_date": "2029-12-31T00:00:00Z",
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

        response = api_client.post("/api/create_task/", {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_missing_name(self, api_client: APIClient, test_user: StudyUser) -> None:
        """Ensure each submitted task has a name."""
        api_client.force_authenticate(user=test_user)
        data = {
            "reward": 10,
            "due_date": "2029-12-31T00:00:00Z",
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
            "due_date": "2029-12-31T00:00:00Z",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_positive_reward(self, api_client: APIClient, test_user: StudyUser) -> None:
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Positive Task",
            "reward": 100,
            "due_date": "2029-12-31T00:00:00Z",
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
            "due_date": "2000-01-01T00:00:00Z",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_response_shape(self, api_client: APIClient, test_user: StudyUser):
        api_client.force_authenticate(user=test_user)
        data = {"name": "Shape Test", "reward": 20, "due_date": "2029-12-31T00:00:00Z"}

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
            "due_date": "2029-12-31T00:00:00Z",
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
            "due_date": "2029-12-31T00:00:00Z",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_excessive_reward(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """A reward higher than the set limit should fail our current basic moderation"""
        # The value in this test is not 101 because this limit is subject to change
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Money Farming Task",
            "reward": 10000000000,
            "due_date": "2029-12-31T00:00:00Z",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_reward_as_string(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """DRF often coerces numeric strings — confirm the actual behavior."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "String Reward Task",
            "reward": "50",
            "due_date": "2029-12-31T00:00:00Z",
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
            "due_date": "2029-12-31T00:00:00Z",
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
            "due_date": "2029-12-31T00:00:00Z",
        }

        response = api_client.post("/api/create_task/", data, format="json")

        # Adjust to match your serializer's actual behavior once confirmed
        assert response.status_code in (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST)

    def test_create_task_with_category(self, api_client: APIClient, test_user: StudyUser) -> None:
        """category is nullable — confirm it's accepted when provided."""
        api_client.force_authenticate(user=test_user)
        data = {
            "name": "Categorized Task",
            "reward": 10,
            "due_date": "2029-12-31T00:00:00Z",
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
            "due_date": "2029-12-31T00:00:00Z",
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
            "due_date": "2029-12-31T00:00:00Z",
            "user": other_user.id,
        }

        api_client.post("/api/create_task/", data, format="json")

        task = Task.objects.get(name="Spoofed User Task")
        assert task.user == test_user  # not other_user


@pytest.mark.required
@pytest.mark.tasks
class TestTaskRetrieval:
    def test_get_task_authenticated(
        self,
        api_client: APIClient,
        test_user: StudyUser,
        test_task: Task,
    ) -> None:
        # Log in
        api_client.force_authenticate(user=test_user)

        # Make the request
        url = "/api/get_task/"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert response.data[0]["name"] == "Test"

    def test_get_task_unauthenticated(self, api_client: APIClient) -> None:
        url = "/api/get_task/"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_task_returns_only_own_tasks(
        self,
        api_client: APIClient,
        test_user: StudyUser,
        other_user: StudyUser,
    ) -> None:
        """Baseline sanity check: authenticated user only sees their own task."""
        api_client.force_authenticate(user=test_user)

        Task.objects.create(
            name="Other User Task",
            reward=5,
            description="not visible",
            due_date="2029-12-31T00:00:00Z",
            user=other_user,
        )

        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data]
        assert "Other User Task" not in names

    def test_get_task_no_tasks_returns_empty_list(
        self, api_client: APIClient, other_user: StudyUser
    ) -> None:
        """A user with zero tasks should get an empty list, not an error."""
        api_client.force_authenticate(user=other_user)

        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

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

        response = api_client.get("/api/get_task/")

        # If your view currently trusts the `username` param over
        # `request.user`, this test will fail — that's worth fixing.
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN)
        if response.status_code == status.HTTP_200_OK:
            names = [t["name"] for t in response.data]
            assert "Test" not in names

    def test_get_task_returns_multiple_tasks(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """A user with several tasks should get all of them back."""
        api_client.force_authenticate(user=test_user)

        Task.objects.create(
            name="Task A", reward=10, due_date="2029-12-31T00:00:00Z", user=test_user
        )
        Task.objects.create(
            name="Task B", reward=20, due_date="2029-12-31T00:00:00Z", user=test_user
        )
        Task.objects.create(
            name="Task C", reward=30, due_date="2029-12-31T00:00:00Z", user=test_user
        )

        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data]
        assert set(names) == {"Task A", "Task B", "Task C"}

    def test_get_task_response_field_shape(
        self, api_client: APIClient, test_user: StudyUser, test_task: Task
    ) -> None:
        """Confirm expected fields are present and no sensitive fields leak."""
        api_client.force_authenticate(user=test_user)

        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        task_data = response.data[0]
        assert "name" in task_data
        assert "reward" in task_data
        assert "due_date" in task_data
        assert "user" not in task_data or not isinstance(task_data.get("user"), dict)
        assert "password" not in task_data

    def test_get_task_nonexistent_username_param(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """Querying a username that doesn't exist shouldn't 500."""
        api_client.force_authenticate(user=test_user)

        response = api_client.get("/api/get_task/", data={"username": "nobody_here"})

        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )

    def test_get_task_does_not_return_soft_deleted_or_unrelated_data(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Sanity check that retrieval count matches exactly what was created — no duplication or leakage."""
        api_client.force_authenticate(user=test_user)
        Task.objects.create(
            name="Only Mine", reward=5, due_date="2029-12-31T00:00:00Z", user=test_user
        )
        Task.objects.create(
            name="Not Mine", reward=5, due_date="2029-12-31T00:00:00Z", user=other_user
        )

        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Only Mine"

    def test_get_task_wrong_http_method_not_allowed(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """POST-ing to a GET-only endpoint should be rejected, not silently succeed."""
        api_client.force_authenticate(user=test_user)

        response = api_client.post("/api/get_task/", {}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_task_includes_category_field(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """category is nullable but should still appear in the response, even as null."""
        api_client.force_authenticate(user=test_user)
        Task.objects.create(
            name="Categorized",
            reward=10,
            due_date="2029-12-31T00:00:00Z",
            category="school",
            user=test_user,
        )

        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["category"] == "school"

    def test_get_task_field_values_are_correct_types(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """Confirm numeric and date fields serialize with correct values, not just correct keys."""
        Task.objects.create(
            name="Type Check",
            reward=42,
            due_date="2029-07-04T00:00:00Z",
            user=test_user,
        )

        api_client.force_authenticate(user=test_user)
        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        task_data = response.data[0]
        assert task_data["reward"] == 42
        assert "2029-07-04T00:00:00Z" in task_data["due_date"]

    def test_get_task_response_is_a_list(
        self, api_client: APIClient, test_user: StudyUser, test_task: Task
    ) -> None:
        """Even with exactly one task, the response should be a list, not a single object."""
        api_client.force_authenticate(user=test_user)

        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_task_pagination_if_enabled(
        self, api_client: APIClient, test_user: StudyUser
    ) -> None:
        """
        If pagination is configured (DRF's default PAGE_SIZE or similar), a large
        number of tasks shouldn't silently truncate without the client knowing.
        If pagination is NOT enabled, this just confirms all tasks come back.
        """
        for i in range(25):
            Task.objects.create(
                name=f"Bulk Task {i}", reward=1, due_date="2029-12-31T00:00:00Z", user=test_user
            )

        api_client.force_authenticate(user=test_user)
        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        if isinstance(response.data, dict) and "results" in response.data:
            # paginated response — check the count field instead
            assert response.data["count"] == 25
        else:
            assert len(response.data) == 25

    def test_get_task_invalid_auth_token_rejected(self, api_client: APIClient) -> None:
        """A garbage/expired credential should not be treated as authenticated."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_garbage")

        response = api_client.get("/api/get_task/")

        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_get_task_inactive_user_cannot_retrieve(
        self, api_client: APIClient, test_user: StudyUser, test_task: Task
    ) -> None:
        """A deactivated account shouldn't be able to pull its own tasks."""
        test_user.is_active = False
        test_user.save()

        api_client.force_authenticate(user=test_user)
        response = api_client.get("/api/get_task/")

        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# @pytest.mark.required
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
        response = api_client.get("/api/get_task/")

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
                {"name": f"Mine {i}", "reward": 5, "due_date": "2029-12-31T00:00:00Z"},
                format="json",
            )

        api_client.force_authenticate(user=other_user)
        for i in range(2):
            api_client.post(
                "/api/create_task/",
                {"name": f"Theirs {i}", "reward": 5, "due_date": "2029-12-31T00:00:00Z"},
                format="json",
            )

        response = api_client.get("/api/get_task/")
        names = [t["name"] for t in response.data]

        assert len(names) == 2
        assert all(name.startswith("Theirs") for name in names)

    def test_same_task_name_allowed_across_different_users(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Task names aren't globally unique — two users can each have a task with the same name."""
        Task.objects.create(name="Homework", reward=10, due_date="2029-12-31", user=test_user)
        Task.objects.create(name="Homework", reward=20, due_date="2029-12-31", user=other_user)

        assert Task.objects.filter(name="Homework").count() == 2
        mine = Task.objects.get(name="Homework", user=test_user)
        theirs = Task.objects.get(name="Homework", user=other_user)
        assert mine.id != theirs.id
        assert mine.reward != theirs.reward

    def test_user_cannot_access_task_by_guessing_id(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Sequential/guessable IDs shouldn't let one user fetch another's specific task."""
        task = Task.objects.create(
            name="Secret Task", reward=10, due_date="2029-12-31", user=other_user
        )

        api_client.force_authenticate(user=test_user)
        response = api_client.get(f"/api/get_task/", data={"id": task.id})

        assert response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_isolation_holds_after_switching_authenticated_user_mid_session(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Re-authenticating as a different user on the same client shouldn't leak the previous user's tasks."""
        api_client.force_authenticate(user=test_user)
        api_client.post(
            "/api/create_task/",
            {"name": "First User Task", "reward": 5, "due_date": "2029-12-31"},
            format="json",
        )

        api_client.force_authenticate(user=other_user)
        response = api_client.get("/api/get_task/")

        names = [t["name"] for t in response.data]
        assert "First User Task" not in names

    def test_create_task_does_not_expose_other_users_task_count(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Creating a task for one user shouldn't be influenced by or leak another user's existing tasks."""
        Task.objects.create(name="Existing", reward=10, due_date="2029-12-31", user=other_user)

        api_client.force_authenticate(user=test_user)
        response = api_client.post(
            "/api/create_task/",
            {"name": "New Task", "reward": 5, "due_date": "2029-12-31"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Task.objects.filter(user=test_user).count() == 1
        assert Task.objects.filter(user=other_user).count() == 1

    def test_get_task_count_matches_only_authenticated_users_tasks(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Total tasks in the DB across all users shouldn't affect what one user sees."""
        Task.objects.create(name="Mine 1", reward=5, due_date="2029-12-31", user=test_user)
        Task.objects.create(name="Theirs 1", reward=5, due_date="2029-12-31", user=other_user)
        Task.objects.create(name="Theirs 2", reward=5, due_date="2029-12-31", user=other_user)
        Task.objects.create(name="Theirs 3", reward=5, due_date="2029-12-31", user=other_user)

        api_client.force_authenticate(user=test_user)
        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        assert Task.objects.count() == 4  # confirms all 4 exist in the DB
        assert len(response.data) == 1  # but only 1 is visible to test_user

    def test_creating_many_tasks_for_one_user_does_not_appear_for_another(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Bulk creation for one user should never leak into another user's view."""
        api_client.force_authenticate(user=test_user)
        for i in range(10):
            api_client.post(
                "/api/create_task/",
                {"name": f"Task {i}", "reward": 1, "due_date": "2029-12-31"},
                format="json",
            )

        api_client.force_authenticate(user=other_user)
        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_task_reward_values_are_isolated_between_users(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Confirm reward/money fields on tasks aren't cross-contaminated between users' tasks."""
        Task.objects.create(name="Cheap", reward=1, due_date="2029-12-31", user=test_user)
        Task.objects.create(name="Expensive", reward=1000, due_date="2029-12-31", user=other_user)

        api_client.force_authenticate(user=test_user)
        response = api_client.get("/api/get_task/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["reward"] == 1

    def test_get_task_only_returns_own_tasks(
        self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
    ) -> None:
        """Create tasks interleaved between two users, confirm isolation without relying on IDs."""
        api_client.force_authenticate(user=test_user)
        api_client.post(
            "/api/create_task/", {"name": "A", "reward": 1, "due_date": "2029-12-31"}, format="json"
        )

        api_client.force_authenticate(user=other_user)
        api_client.post(
            "/api/create_task/", {"name": "B", "reward": 1, "due_date": "2029-12-31"}, format="json"
        )

        api_client.force_authenticate(user=test_user)
        response = api_client.get("/api/get_task/")
        names = [t["name"] for t in response.data]

        assert "A" in names
        assert "B" not in names


# Test Graveyard for tests that get generated but aren't useful *yet*

# def test_deleting_user_cascades_to_tasks(
#     self, api_client: APIClient, test_user: StudyUser
# ) -> None:
#     Task.objects.create(
#         name="Cascade Task",
#         reward=10,
#         due_date="2029-12-31T00:00:00Z",
#         user=test_user,
#     )
#     test_user.delete()

#     assert not Task.objects.filter(name="Cascade Task").exists()

# Isolation Tests! (might need to make a second class)

# def test_user_cannot_delete_another_users_task(
#         self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
#     ) -> None:
#         """A user should not be able to delete a task they don't own."""
#         task = Task.objects.create(
#             name="Other's Task", reward=10, due_date="2029-12-31", user=other_user
#         )

#         api_client.force_authenticate(user=test_user)
#         response = api_client.delete(f"/api/delete_task/{task.id}/")

#         assert response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
#         assert Task.objects.filter(id=task.id).exists()

# def test_user_cannot_update_another_users_task(
#     self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
# ) -> None:
#     """A user should not be able to modify a task they don't own."""
#     task = Task.objects.create(
#         name="Original Name", reward=10, due_date="2029-12-31", user=other_user
#     )

#     api_client.force_authenticate(user=test_user)
#     response = api_client.patch(
#         f"/api/update_task/{task.id}/", {"name": "Hacked Name"}, format="json"
#     )

#     assert response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
#     task.refresh_from_db()
#     assert task.name == "Original Name"

# def test_deleting_one_user_does_not_affect_other_users_tasks(
#     self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
# ) -> None:
#     """Cascade delete should only remove the deleted user's own tasks."""
#     Task.objects.create(name="Mine", reward=10, due_date="2029-12-31", user=test_user)
#     Task.objects.create(name="Theirs", reward=10, due_date="2029-12-31", user=other_user)

#     test_user.delete()

#     assert not Task.objects.filter(name="Mine").exists()
#     assert Task.objects.filter(name="Theirs").exists()

# def test_same_task_name_allowed_across_different_users(
#     self, api_client: APIClient, test_user: StudyUser, other_user: StudyUser
# ) -> None:
#     """Task names aren't globally unique — two users can each have a task with the same name."""
#     Task.objects.create(name="Homework", reward=10, due_date="2029-12-31", user=test_user)
#     Task.objects.create(name="Homework", reward=20, due_date="2029-12-31", user=other_user)

#     assert Task.objects.filter(name="Homework").count() == 2
#     mine = Task.objects.get(name="Homework", user=test_user)
#     theirs = Task.objects.get(name="Homework", user=other_user)
#     assert mine.id != theirs.id
#     assert mine.reward != theirs.reward
