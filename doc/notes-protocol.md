# Behringer X-AIR /MIDAS M-AIR OSC Protocoll Notes


## Parameters


### Channel Level

/ch/<nn>/mix/fader  0.0 .. 1.0 (0.75 ~= 0db )

<nn> = 01 .. 18 (two digits with leading zero)


### Main Mix Level:

/lr/mix/fader


###Main Mix Mute

/lr/mix/on [0, 1]


## Subscribing to Parameter Updates

Example:

    /subscribe /ch/01/mix/fader <frequency>

`<frequency>` is in roughly 0.5 Hz units (e.g. one update per 500 ms)

Will send parameter updates to the client at rate of <frequency> for about 10 seconds.
