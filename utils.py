def record_state(is_in_position, position):
    file = open('state.txt', 'w')
    file.write(f"{is_in_position},{position}")
    file.close()
