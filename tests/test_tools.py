"""Unit tests for tool handlers."""
import pytest
from agents.player.tools import handle_game_invitation, parity_choose, notify_match_result
from shared.jsonrpc import JSONRPCError
from agents.player.state import init_state, get_state


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test."""
    init_state("TestAgent")
    yield
    # Cleanup after test


class TestHandleGameInvitation:
    """Test handle_game_invitation tool."""
    
    def test_valid_invitation(self):
        """Test handling valid game invitation."""
        params = {
            "game_id": "game123",
            "from_player": "league",
            "invitation_id": "inv001"
        }
        
        result = handle_game_invitation(params)
        
        assert result["type"] == "GAME_JOIN_ACK"
        assert result["accepted"] is True
        assert result["game_id"] == "game123"
        assert result["invitation_id"] == "inv001"
        
        # Verify state was updated
        state = get_state()
        assert "game123" in state.invitations
        assert state.invitations["game123"].game_id == "game123"
    
    def test_invitation_with_extra_fields(self):
        """Test invitation accepts extra fields."""
        params = {
            "game_id": "game456",
            "from_player": "league",
            "invitation_id": "inv002",
            "extra_field": "should_be_accepted",
            "nested": {"foo": "bar"}
        }
        
        result = handle_game_invitation(params)
        
        assert result["type"] == "GAME_JOIN_ACK"
        assert result["accepted"] is True
        
        # Extra fields should be stored in state
        state = get_state()
        assert state.invitations["game456"].extra_fields["extra_field"] == "should_be_accepted"
    
    def test_invitation_without_params(self):
        """Test invitation without params raises error."""
        with pytest.raises(JSONRPCError) as exc_info:
            handle_game_invitation(None)
        
        assert exc_info.value.code == -32602  # Invalid params
    
    def test_invitation_with_invalid_params_type(self):
        """Test invitation with non-dict params raises error."""
        with pytest.raises(JSONRPCError) as exc_info:
            handle_game_invitation([1, 2, 3])
        
        assert exc_info.value.code == -32602


class TestParityChoose:
    """Test parity_choose tool."""
    
    def test_valid_parity_choice(self):
        """Test making parity choice."""
        params = {"game_id": "game789"}
        
        result = parity_choose(params)
        
        assert result["type"] == "RESPONSE_PARITY_CHOOSE"
        assert result["choice"] in ["even", "odd"]
        assert result["game_id"] == "game789"
        
        # Verify state was updated
        state = get_state()
        assert "game789" in state.choices
        assert state.choices["game789"].game_id == "game789"
    
    def test_deterministic_choice(self):
        """Test same game_id gives same choice."""
        params = {"game_id": "deterministic_test"}
        
        result1 = parity_choose(params)
        choice1 = result1["choice"]
        
        # Reset and choose again
        init_state("TestAgent")
        result2 = parity_choose(params)
        choice2 = result2["choice"]
        
        assert choice1 == choice2
    
    def test_different_games_vary(self):
        """Test different game_ids can give different choices."""
        choices = set()
        
        for i in range(20):
            params = {"game_id": f"game_{i}"}
            result = parity_choose(params)
            choices.add(result["choice"])
        
        # Should have both even and odd
        assert len(choices) == 2
        assert "even" in choices
        assert "odd" in choices
    
    def test_parity_without_params(self):
        """Test parity choice without params raises error."""
        with pytest.raises(JSONRPCError) as exc_info:
            parity_choose(None)
        
        assert exc_info.value.code == -32602
    
    def test_parity_with_extra_fields(self):
        """Test parity choice accepts extra fields."""
        params = {
            "game_id": "game999",
            "extra_data": "should_be_accepted"
        }
        
        result = parity_choose(params)
        
        assert result["type"] == "RESPONSE_PARITY_CHOOSE"
        assert result["choice"] in ["even", "odd"]


class TestNotifyMatchResult:
    """Test notify_match_result tool."""
    
    def test_win_result(self):
        """Test recording a win."""
        params = {
            "game_id": "game001",
            "winner": "TestAgent",  # Matches our test agent name
            "details": {"rolled": 7, "parity": "odd"}
        }
        
        result = notify_match_result(params)
        
        assert result["ok"] is True
        
        # Verify stats updated
        state = get_state()
        stats = state.get_stats()
        assert stats.games_played == 1
        assert stats.wins == 1
        assert stats.losses == 0
        assert stats.draws == 0
        assert stats.win_rate == 1.0
    
    def test_loss_result(self):
        """Test recording a loss."""
        params = {
            "game_id": "game002",
            "winner": "OtherAgent",
            "details": {"rolled": 4, "parity": "even"}
        }
        
        result = notify_match_result(params)
        
        assert result["ok"] is True
        
        # Verify stats updated
        state = get_state()
        stats = state.get_stats()
        assert stats.games_played == 1
        assert stats.wins == 0
        assert stats.losses == 1
        assert stats.win_rate == 0.0
    
    def test_draw_result(self):
        """Test recording a draw."""
        params = {
            "game_id": "game003",
            "winner": None,
            "details": {"rolled": 6, "parity": "even"}
        }
        
        result = notify_match_result(params)
        
        assert result["ok"] is True
        
        # Verify stats updated
        state = get_state()
        stats = state.get_stats()
        assert stats.games_played == 1
        assert stats.wins == 0
        assert stats.losses == 0
        assert stats.draws == 1
    
    def test_multiple_results(self):
        """Test multiple match results update stats correctly."""
        # Win
        notify_match_result({
            "game_id": "g1",
            "winner": "TestAgent",
            "details": {}
        })
        
        # Loss
        notify_match_result({
            "game_id": "g2",
            "winner": "Other",
            "details": {}
        })
        
        # Draw
        notify_match_result({
            "game_id": "g3",
            "winner": None,
            "details": {}
        })
        
        # Win
        notify_match_result({
            "game_id": "g4",
            "winner": "TestAgent",
            "details": {}
        })
        
        state = get_state()
        stats = state.get_stats()
        assert stats.games_played == 4
        assert stats.wins == 2
        assert stats.losses == 1
        assert stats.draws == 1
        assert stats.win_rate == 0.5
    
    def test_result_without_params(self):
        """Test result without params raises error."""
        with pytest.raises(JSONRPCError) as exc_info:
            notify_match_result(None)
        
        assert exc_info.value.code == -32602
    
    def test_result_with_extra_fields(self):
        """Test result accepts extra fields."""
        params = {
            "game_id": "game888",
            "winner": "TestAgent",
            "details": {"rolled": 5},
            "extra_metadata": "should_be_stored"
        }
        
        result = notify_match_result(params)
        
        assert result["ok"] is True
        
        # Extra fields should be in history
        state = get_state()
        assert "game888" in state.results
        assert state.results["game888"].extra_fields["extra_metadata"] == "should_be_stored"
