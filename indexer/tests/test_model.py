from model import InternalServerException, ServiceUnavailableException  

# Test for InternalServerException
def test_internal_server_exception():
    message = "An internal server error occurred"
    exception = InternalServerException(message)

    assert exception.message == message
    assert exception.status_code == 500
    assert str(exception) == message


# Test for ServiceUnavailableException
def test_service_unavailable_exception():
    message = "Service is unavailable"
    exception = ServiceUnavailableException(message)

    assert exception.message == message
    assert exception.status_code == 503
    assert str(exception) == message
