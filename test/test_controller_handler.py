"""Unittests (pytest format) for the controller_handler"""
from unittest.mock import Mock

import pytweening
from numpy import linspace

from exceptions.exceptions import ControllerSetLEDException, InvalidRequestException
from color import Color
from config import FPS
from controller_handler import ControllerHandler
from controller import DMX_controller

START_COLOR = Color(201, 117, 128)
FINAL_COLOR = Color(193, 109, 120)
DEFAULT_DURATION = 300
DEFAULT_EASE = 'linear'
DEFAULT_ANIMATE_JSON = {'color': '#C9751C', 'duration': '15', 'ease': 'linear'}
DEFAULT_ANIMATION = [Color(r=201, g=117, b=128), Color(r=200, g=116, b=127),
                     Color(r=199, g=115, b=126), Color(r=198, g=114, b=125),
                     Color(r=197, g=113, b=124), Color(r=196, g=112, b=123),
                     Color(r=195, g=111, b=122), Color(r=194, g=110, b=121),
                     Color(r=193, g=109, b=120)]
DEFAULT_TOGGLE_JSON = {'color': '#C9751C'}


def get_controller_mock():
    """Default method to get a controller with all methods mocked"""
    controller_mock = DMX_controller(1)
    controller_mock.make_frame = Mock()
    controller_mock.send_start = Mock()
    controller_mock.send_data = Mock()
    controller_mock.send_data_skip = Mock()
    controller_mock.send_single = Mock()
    return controller_mock


def get_handler():
    """Method which returns a controller_handler and a controller"""
    controller = get_controller_mock()
    return ControllerHandler(controller), controller


'''                                  Test generate_animation                              '''


# pylint disable: C0111
def test_generate_animation_same_colors():
    # Arrange
    handler, _ = get_handler()

    # Act
    animation = handler.generate_animation(START_COLOR, START_COLOR, DEFAULT_DURATION, DEFAULT_EASE)
    # Assert
    assert all([x == animation[0] for x in animation])


def test_generate_animation_different_colors():
    # Arrange
    handler, _ = get_handler()

    # Act
    animation = handler.generate_animation(START_COLOR, FINAL_COLOR, DEFAULT_DURATION, DEFAULT_EASE)
    # Assert
    assert not all([x == animation[0] for x in animation])


def test_generate_animation_correct_animation():
    # Arrange
    handler, _ = get_handler()
    diff = FINAL_COLOR - START_COLOR
    tween = getattr(pytweening, DEFAULT_EASE)
    correct_animation = [START_COLOR + diff * tween(step)
                         for step in linspace(0, 1, int(FPS * DEFAULT_DURATION / 1000))]

    # Act
    animation = handler.generate_animation(START_COLOR, FINAL_COLOR, DEFAULT_DURATION, DEFAULT_EASE)
    # Assert
    assert animation == correct_animation


def test_generate_animation_correct_amount():
    # Arrange
    handler, _ = get_handler()
    steps = len(linspace(0, 1, int(FPS * DEFAULT_DURATION / 1000)))

    # Act
    animation = handler.generate_animation(START_COLOR, FINAL_COLOR, DEFAULT_DURATION, DEFAULT_EASE)

    # Assert
    assert len(animation) == steps


def test_generate_animation_no_steps():
    """
    Method should have only the final color in the list, since the duration is too short to allow
    even a single step
    """
    # Arrange
    handler, _ = get_handler()
    duration = 800 / FPS

    # Act
    animation = handler.generate_animation(START_COLOR, FINAL_COLOR, duration, DEFAULT_EASE)

    # Assert
    assert animation == [FINAL_COLOR]


def test_generate_animation_one_step():
    """
    Method should have only the start color and the final color in the list,
    since there is only one step possible with the duration
    """
    # Arrange
    handler, _ = get_handler()
    duration = 1000 / FPS

    # Act
    animation = handler.generate_animation(START_COLOR, FINAL_COLOR, duration, DEFAULT_EASE)

    # Assert
    assert animation == [START_COLOR, FINAL_COLOR]


def test_generate_animation_different_ease():
    # Arrange
    handler, _ = get_handler()
    ease = "easeInQuad"
    diff = FINAL_COLOR - START_COLOR
    tween = getattr(pytweening, ease)
    wrong_tween = getattr(pytweening, DEFAULT_EASE)
    correct_animation = [START_COLOR + diff * tween(step)
                         for step in linspace(0, 1, int(FPS * DEFAULT_DURATION / 1000))]
    wrong_animation = [START_COLOR + diff * wrong_tween(step)
                       for step in linspace(0, 1, int(FPS * DEFAULT_DURATION / 1000))]

    # Act
    animation = handler.generate_animation(START_COLOR, FINAL_COLOR, DEFAULT_DURATION, ease)

    # Assert
    assert correct_animation == animation
    assert wrong_animation != animation


def test_generate_animation_no_ease():
    """ Method that tests if the correct exception is thrown when no ease is given """
    # Arrange
    handler, _ = get_handler()
    ease = None
    exception = None

    # Act
    try:
        handler.generate_animation(START_COLOR, FINAL_COLOR, DEFAULT_DURATION, ease)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == TypeError


def test_generate_animation_wrong_ease():
    """ Method that tests if the correct exception is thrown when no ease is given """
    # Arrange
    handler, _ = get_handler()
    ease = "superQuadraticLogarithmic"
    exception = None

    # Act
    try:
        handler.generate_animation(START_COLOR, FINAL_COLOR, DEFAULT_DURATION, ease)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == AttributeError


'''                                  Test play_animation                                    '''


def test_play_animation():
    """ play_animation should call handler.set_led as many times as there are animation frames. """
    # Arrange
    handler, _ = get_handler()
    handler.set_led = Mock()

    # Act
    animation = handler.generate_animation(START_COLOR, FINAL_COLOR, DEFAULT_DURATION, DEFAULT_EASE)
    handler.play_animation(animation)

    # Assert
    assert handler.set_led.call_count == len(animation)


def test_set_led():
    """
    set_led should call controller.send_start with the rgb values, and should call make_frame twice.
    """
    # Arrange
    handler, controller = get_handler()
    r, g, b = START_COLOR.r, START_COLOR.g, START_COLOR.b

    # Act
    handler.set_led(START_COLOR)

    # Assert
    # todo update for new changes
    # controller.send_start.assert_called_once_with(0, [r, g, b, 0, 0, 0])
    # assert controller.make_frame.call_count == 2


def test_set_led_raise_correct_exception():
    """ if make_frame raise a NameError, set_led should raise a ControllerSetLEDException """
    # Arrange
    handler, controller = get_handler()
    controller.make_frame = Mock(side_effect=NameError('foo'))
    exception = None

    # Act
    try:
        handler.set_led(START_COLOR)
    except ControllerSetLEDException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == NameError


'''                                        Test animate                                '''


def test_animate_correct_json():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'duration': '15', 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except Exception as e:
        exception = e

    # Assert
    assert exception is None


def test_animate_wrong_color():
    # Arrange
    handler, _ = get_handler()
    json = {'color': 'wrong', 'duration': '15', 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == ValueError


def test_animate_wrong_color_hex():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751G', 'duration': '15', 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == ValueError


def test_animate_wrong_color_type():
    # Arrange
    handler, _ = get_handler()
    json = {'color': {'r': '14', 'g': '23', 'b': '69'}, 'duration': '15', 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == AttributeError


def test_animate_wrong_color_none():
    # Arrange
    handler, _ = get_handler()
    json = {'color': None, 'duration': '15', 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == AttributeError


def test_animate_wrong_duration_empty():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'duration': '', 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == ValueError


def test_animate_wrong_duration_none():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'duration': None, 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == TypeError


def test_animate_wrong_duration_type():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'duration': 'string', 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == ValueError


def test_animate_wrong_duration_missing():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'ease': 'linear'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == KeyError


def test_animate_wrong_ease_empty():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'duration': '15', 'ease': ''}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == AttributeError


def test_animate_wrong_ease_none():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'duration': '15', 'ease': None}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == TypeError


def test_animate_wrong_ease_missing():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'duration': '15'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == KeyError


def test_animate_wrong_ease_text():
    # Arrange
    handler, _ = get_handler()
    json = {'color': '#C9751C', 'duration': '15', 'ease': 'quadraticallyCrazy'}
    exception = None

    # Act
    try:
        handler.animate(json)
    except InvalidRequestException as e:
        exception = e

    # Assert
    assert exception is not None
    assert type(exception.inner_exception) == AttributeError


def test_animate_calls_generate():
    # Arrange
    handler, _ = get_handler()

    handler.generate_animation = Mock(return_value=DEFAULT_ANIMATION)

    # Act
    handler.animate(DEFAULT_ANIMATE_JSON)

    # Assert
    handler.generate_animation.assert_called_once()


def test_animate_calls_play():
    # Arrange
    handler, _ = get_handler()

    handler.generate_animation = Mock(return_value=DEFAULT_ANIMATION)
    handler.play_animation = Mock()

    # Act
    handler.animate(DEFAULT_ANIMATE_JSON)

    # Assert
    handler.play_animation.assert_called_once()


def test_animate_current_color_set():
    # Arrange
    handler, _ = get_handler()
    handler.generate_animation = Mock(return_value=DEFAULT_ANIMATION)
    handler.play_animation = Mock()

    # Act
    handler.animate(DEFAULT_ANIMATE_JSON)

    # Assert
    assert handler.current_color == DEFAULT_ANIMATION[-1]


def test_toggle_setled_called():
    # Arrange
    handler, _ = get_handler()
    handler.set_led = Mock()

    # Act
    handler.toggle()

    # Assert
    handler.set_led.assert_called_once()
