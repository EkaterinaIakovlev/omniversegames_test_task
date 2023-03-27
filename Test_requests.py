import pytest
import requests
import uuid


class TestTaskOmniverseGames:
    url_base = "https://testers-task.omniversegames.ru/"
    battle_header = ""
    battle_id = ""
    # Preparing test data, positive ang negative
    login_data = [
        ("example_user", "example_password"),
        ("wrong_user", "example_password"),
        ("example_user", "wrong_password"),
        ("wrong_user", "wrong_password"),
        ("", ""),
        (123, 123),
        (True, False)
    ]
    user1 = str(uuid.uuid4())
    user2 = str(uuid.uuid4())
    uuid_data = [
        (user1, user2),
        (user2, user1),
        (user1, user1),
        (user1, "1234"),
        ("", ""),
        (123, 1234)
    ]
    battle_end_data = [
        (user1, user2, True, False),
        (user1, user2, False, True),
        (user1, user2, False, False),
        (user1, user2, True, True),
        (user1, user2, "", True),
        (str(uuid.uuid4()), str(uuid.uuid4()), True, False),
        ("asdf", str(uuid.uuid4()), str(uuid.uuid4()), False),
        ("", "", True, "")
    ]

    # Preparing valid data to not duplicate code
    def setup(self):
        correct_auth_data = {
            "username": "example_user",
            "password": "example_password"
        }
        url = self.url_base + "login"
        response = requests.post(url, json=correct_auth_data)
        self.battle_header = {
            "Authorization": f"Bearer {response.json()['access_token']}"
        }
        correct_battle_start_data = {
            "users": [self.user1, self.user2]
        }
        url = self.url_base + "battle/start"
        battle_start_response = requests.post(url, headers=self.battle_header, json=correct_battle_start_data)
        self.battle_id = battle_start_response.json()["battle_id"]

    # Run test with valid and not valid username and password
    @pytest.mark.parametrize('username, password', login_data)
    def test_authorization(self, username, password):
        url = self.url_base + "login"
        data = {
            "username": username,
            "password": password
        }
        auth_response = requests.post(url, json=data)
        if auth_response.status_code == 200:
            assert len(auth_response.json()["access_token"]) != 0  # token isn't empty
            assert auth_response.json()["token_type"] == "bearer"  # token has correct type
        elif auth_response.status_code == 401:
            assert auth_response.json()[
                       "detail"] == "Invalid username or password"  # mistakes in username or password give the correct error

    # Run test with valid and not valid user id
    @pytest.mark.parametrize('user_id1, user_id2', uuid_data)
    def test_battle_start(self, user_id1, user_id2):
        url = self.url_base + "battle/start"
        data = {"users": [user_id1, user_id2]}
        assert user_id1 != user_id2  # User can't start battle with himself
        battle_start_response = requests.post(url, headers=self.battle_header, json=data)
        assert battle_start_response.status_code == 200
        assert len(battle_start_response.json()["battle_id"]) != 0  # Battle id isn't empty
        assert uuid.UUID(str(battle_start_response.json()["battle_id"]))  # Battle id has correct format

    # Run test with valid and not valid users id and is_won parameters
    @pytest.mark.parametrize('user_id1, user_id2, first_won, second_won', battle_end_data)
    def test_battle_end(self, user_id1, user_id2, first_won, second_won):
        url = self.url_base + "battle/end"
        assert first_won != second_won  # Both can't win or lose at the same time
        data = {
            "battle_id": f"{self.battle_id}",
            "results": {
                f"{user_id1}": {
                    "is_won": first_won
                },
                f"{user_id2}": {
                    "is_won": second_won
                }
            }
        }
        battle_end_response = requests.post(url, headers=self.battle_header, json=data)
        assert battle_end_response.status_code == 200 or battle_end_response.status_code == 400
        if battle_end_response.status_code == 200:
            assert battle_end_response.json()["success"] is True  # battle finished successful
            assert battle_end_response.json()["battle"] is not None  # battle object isn't empty
            battle_info = battle_end_response.json()["battle"]
            assert battle_info["id"] == self.battle_id  # Check that finished indicated battle
        elif battle_end_response.status_code == 400:
            assert battle_end_response.json()["detail"] == "User didn\'t participate this battle"  # mistakes in uuid give the correct error
