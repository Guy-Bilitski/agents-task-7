"""Unit tests for state management."""
import pytest
import threading
import time
from agent.state import (
    init_state,
    get_state,
    AgentState,
    deterministic_parity_choice,
)


@pytest.fixture
def fresh_state():
    """Create a fresh state for testing."""
    init_state("TestAgent")
    return get_state()


class TestAgentState:
    """Test AgentState class."""
    
    def test_initialization(self, fresh_state):
        """Test state initializes correctly."""
        assert fresh_state._display_name == "TestAgent"
        assert fresh_state._last_invitation is None
        assert fresh_state._current_choice is None
        assert fresh_state._last_result is None
        assert fresh_state._stats.games_played == 0
        assert fresh_state._stats.wins == 0
        assert fresh_state._stats.losses == 0
        assert fresh_state._stats.draws == 0
        assert len(fresh_state._history) == 0
    
    def test_record_invitation(self, fresh_state):
        """Test recording game invitation."""
        fresh_state.record_invitation(
            game_id="game123",
            from_player="league",
            invitation_id="inv001",
            extra_fields={"custom": "data"}
        )
        
        assert fresh_state._last_invitation is not None
        assert fresh_state._last_invitation.game_id == "game123"
        assert fresh_state._last_invitation.from_player == "league"
        assert fresh_state._last_invitation.invitation_id == "inv001"
        assert fresh_state._last_invitation.extra_fields == {"custom": "data"}
        
        # Check history
        assert len(fresh_state._history) == 1
        assert fresh_state._history[0]["event"] == "invitation"
    
    def test_record_choice(self, fresh_state):
        """Test recording parity choice."""
        fresh_state.record_choice(
            game_id="game456",
            choice="even",
            extra_fields={}
        )
        
        assert fresh_state._current_choice is not None
        assert fresh_state._current_choice.game_id == "game456"
        assert fresh_state._current_choice.choice == "even"
        
        # Check history
        assert len(fresh_state._history) == 1
        assert fresh_state._history[0]["event"] == "parity_choice"
    
    def test_record_result_win(self, fresh_state):
        """Test recording a win."""
        fresh_state.record_result(
            game_id="game789",
            winner="TestAgent",  # Matches display name
            details={"rolled": 7},
            extra_fields={}
        )
        
        assert fresh_state._last_result is not None
        assert fresh_state._last_result.game_id == "game789"
        assert fresh_state._last_result.winner == "TestAgent"
        
        stats = fresh_state.get_stats()
        assert stats.games_played == 1
        assert stats.wins == 1
        assert stats.losses == 0
        assert stats.draws == 0
        assert stats.win_rate == 1.0
    
    def test_record_result_loss(self, fresh_state):
        """Test recording a loss."""
        fresh_state.record_result(
            game_id="game999",
            winner="OtherAgent",
            details={},
            extra_fields={}
        )
        
        stats = fresh_state.get_stats()
        assert stats.games_played == 1
        assert stats.wins == 0
        assert stats.losses == 1
        assert stats.draws == 0
        assert stats.win_rate == 0.0
    
    def test_record_result_draw(self, fresh_state):
        """Test recording a draw."""
        fresh_state.record_result(
            game_id="game000",
            winner=None,
            details={},
            extra_fields={}
        )
        
        stats = fresh_state.get_stats()
        assert stats.games_played == 1
        assert stats.wins == 0
        assert stats.losses == 0
        assert stats.draws == 1
    
    def test_get_history(self, fresh_state):
        """Test getting event history."""
        fresh_state.record_invitation("g1", "league", "inv1", {})
        fresh_state.record_choice("g1", "even", {})
        fresh_state.record_result("g1", "TestAgent", {}, {})
        
        history = fresh_state.get_history()
        assert len(history) == 3
        assert history[0]["event"] == "invitation"
        assert history[1]["event"] == "parity_choice"
        assert history[2]["event"] == "match_result"


class TestThreadSafety:
    """Test thread safety of state management."""
    
    def test_concurrent_invitations(self, fresh_state):
        """Test multiple threads can record invitations safely."""
        def record_invitation(i):
            fresh_state.record_invitation(
                game_id=f"game_{i}",
                from_player="league",
                invitation_id=f"inv_{i}",
                extra_fields={}
            )
        
        threads = []
        for i in range(50):
            t = threading.Thread(target=record_invitation, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All invitations should be recorded in history
        assert len(fresh_state.get_history()) == 50
    
    def test_concurrent_choices(self, fresh_state):
        """Test multiple threads can record choices safely."""
        def record_choice(i):
            choice = "even" if i % 2 == 0 else "odd"
            fresh_state.record_choice(
                game_id=f"game_{i}",
                choice=choice,
                extra_fields={}
            )
        
        threads = []
        for i in range(50):
            t = threading.Thread(target=record_choice, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(fresh_state.get_history()) == 50
    
    def test_concurrent_results(self, fresh_state):
        """Test multiple threads can record results safely."""
        def record_result(i):
            winner = "TestAgent" if i % 3 == 0 else ("OtherAgent" if i % 3 == 1 else None)
            fresh_state.record_result(
                game_id=f"game_{i}",
                winner=winner,
                details={},
                extra_fields={}
            )
        
        threads = []
        for i in range(60):  # 20 wins, 20 losses, 20 draws
            t = threading.Thread(target=record_result, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        stats = fresh_state.get_stats()
        assert stats.games_played == 60
        assert stats.wins == 20
        assert stats.losses == 20
        assert stats.draws == 20
        assert abs(stats.win_rate - (20/60)) < 0.001


class TestDeterministicChoice:
    """Test deterministic parity choice function."""
    
    def test_deterministic_for_same_game_id(self):
        """Test same game_id always gives same choice."""
        game_id = "test_game_123"
        
        choice1 = deterministic_parity_choice(game_id)
        choice2 = deterministic_parity_choice(game_id)
        choice3 = deterministic_parity_choice(game_id)
        
        assert choice1 == choice2 == choice3
        assert choice1 in ["even", "odd"]
    
    def test_different_game_ids_vary(self):
        """Test different game_ids give varied choices."""
        choices = set()
        
        for i in range(100):
            choice = deterministic_parity_choice(f"game_{i}")
            choices.add(choice)
        
        # Should have both even and odd
        assert len(choices) == 2
        assert "even" in choices
        assert "odd" in choices
    
    def test_empty_game_id(self):
        """Test empty game_id still works."""
        choice = deterministic_parity_choice("")
        assert choice in ["even", "odd"]
    
    def test_special_characters(self):
        """Test game_id with special characters."""
        choice = deterministic_parity_choice("game-123!@#$%^&*()")
        assert choice in ["even", "odd"]


class TestStatistics:
    """Test statistics calculations."""
    
    def test_win_rate_all_wins(self, fresh_state):
        """Test win rate with all wins."""
        for i in range(10):
            fresh_state.record_result(f"g{i}", "TestAgent", {}, {})
        
        stats = fresh_state.get_stats()
        assert stats.win_rate == 1.0
    
    def test_win_rate_all_losses(self, fresh_state):
        """Test win rate with all losses."""
        for i in range(10):
            fresh_state.record_result(f"g{i}", "OtherAgent", {}, {})
        
        stats = fresh_state.get_stats()
        assert stats.win_rate == 0.0
    
    def test_win_rate_mixed(self, fresh_state):
        """Test win rate with mixed results."""
        # 3 wins, 2 losses, 1 draw
        fresh_state.record_result("g1", "TestAgent", {}, {})
        fresh_state.record_result("g2", "TestAgent", {}, {})
        fresh_state.record_result("g3", "TestAgent", {}, {})
        fresh_state.record_result("g4", "OtherAgent", {}, {})
        fresh_state.record_result("g5", "OtherAgent", {}, {})
        fresh_state.record_result("g6", None, {}, {})
        
        stats = fresh_state.get_stats()
        assert stats.games_played == 6
        assert stats.wins == 3
        assert stats.losses == 2
        assert stats.draws == 1
        assert stats.win_rate == 0.5
    
    def test_win_rate_no_games(self, fresh_state):
        """Test win rate with no games."""
        stats = fresh_state.get_stats()
        assert stats.games_played == 0
        assert stats.win_rate == 0.0
