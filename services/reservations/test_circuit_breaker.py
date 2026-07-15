import time
from app.main import CircuitBreaker, CircuitState

def test_circuit_breaker_initial_state():
    cb = CircuitBreaker(failure_threshold=3, reset_seconds=10.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True

def test_circuit_breaker_opens_after_failures():
    cb = CircuitBreaker(failure_threshold=3, reset_seconds=10.0)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True
    
    # Third failure should open the circuit
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False

def test_circuit_breaker_half_open_transition(monkeypatch):
    cb = CircuitBreaker(failure_threshold=3, reset_seconds=0.1)
    
    # Trigger open state
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False
    
    # Simulate time passing beyond reset_seconds
    time.sleep(0.15)
    
    # Should transition to half-open
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN

def test_circuit_breaker_closes_on_success_after_half_open():
    cb = CircuitBreaker(failure_threshold=3, reset_seconds=0.0)
    
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    
    # Immediately check allow_request to trigger half-open
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN
    
    # A successful request should close the circuit
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0

def test_circuit_breaker_reopens_on_failure_after_half_open():
    cb = CircuitBreaker(failure_threshold=3, reset_seconds=0.0)
    
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    
    # Immediately check allow_request to trigger half-open
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN
    
    # A failure should immediately reopen the circuit
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
