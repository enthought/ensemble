from ensemble.ctf.editor import ALPHA_DEFAULT, create_function

from ensemble.ctf.editor_tools import AlphaFunctionEditorTool


def init_alpha_function_tool():
    alpha_function = create_function(ALPHA_DEFAULT)
    return AlphaFunctionEditorTool(function=alpha_function)


def test_move_first_point():
    # The first point in the alpha curve cannot move in the x-direction
    tool = init_alpha_function_tool()

    dy = 0.5  # Note the first point is at y = 0, so we need 0 < dy < 1
    index = 0
    init_position = tool.function.value_at(index)
    tool.set_delta((index, init_position), 0.1, dy)

    final_position = tool.function.value_at(index)
    # The x-position is pinned
    assert final_position[0] == init_position[0]
    assert final_position[1] == (init_position[1] + dy)


def test_move_last_point():
    # The last point in the alpha curve cannot move in the x-direction
    tool = init_alpha_function_tool()

    dy = -0.5  # Note the last point is at y = 1, so we need 0 < dy < -1
    index = tool.function.size() - 1
    init_position = tool.function.value_at(index)
    tool.set_delta((index, init_position), -0.1, dy)

    final_position = tool.function.value_at(index)
    # The x-position is pinned
    assert final_position[0] == init_position[0]
    assert final_position[1] == (init_position[1] + dy)


def test_node_doesnt_move_below_zero():
    tool = init_alpha_function_tool()

    index = 1
    middle_point = (0.5, 0)
    tool.function.insert(middle_point)

    assert tool.function.size() == 3
    assert tool.function.value_at(index) == middle_point

    eps = 0.001
    tool.set_delta((index, middle_point), 0, -eps)

    assert tool.function.value_at(index) == middle_point
