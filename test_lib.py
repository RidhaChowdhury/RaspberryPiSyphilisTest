def parse_data(data):
    data = data.split(';')

    # Data comes back in the following structure:'Pda801B69Bu; ba842C1C4f,14,204
    # Where the first part 801B69Bu is the potential in hex form with the u denoting microvolts
    # and the second part 842C1C4f is the current in hex form with the f denoting femtoamps
    # filter out returns that have other unit characters
    
    # Parse the potential and current
    if data[0][-1] != 'u' or data[1][data[1].index(',') - 1] != 'f':
        return None

    potential = int(data[0][3:-1], 16)
    current = int(data[1][3:data[1].index(',') - 1], 16)

    return potential, current

cv = [
    "e",
    "var c",
    "var p",
    "set_pgstat_chan 1",
    "set_pgstat_mode 0",
    "set_pgstat_chan 0",
    "set_pgstat_mode 2",
    "set_max_bandwidth 40",
    "set_range_minmax da -500m 800m",
    "set_range ba 9218750p",
    "set_autoranging ba 9218750p 2950u",
    "set_e 0",
    "cell_on",
    "meas_loop_ca p c 0 500m 2",
    "pck_start",
    "pck_add p",
    "pck_add c",
    "pck_end",
    "endloop",
    "meas_loop_cv p c 0 -500m 800m 10m 100m nscans(1)",
    "pck_start",
    "pck_add p",
    "pck_add c",
    "pck_end",
    "endloop",
    "on_finished:",
    "cell_off",
    "",
]