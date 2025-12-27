# Hangar Buddy UI Configurator

## Summary

This is a simple UI that will allow the user to configure their HangarBuddy.

It is intended to be run when the IP address is known, or the Raspberry Pi is in Access Point Mode.

Most users will be using a mobile phone to access this, so mobile and reactive pages are the primary concern.

The UI will be simple, concentrating on configuration values set in `HangarBuddy.config`. Not all values will be configurable.

## Components

We are going to create a new project inside the `configurator` sub-folder.

This is going to be a Typescript/Vite/Node based project that will run on a Raspberry Pi (Bookworm) running Node 18.

## Visual Style And Resolution

There is an existing `style.css` file from a previous project that will be used as the basis. This is to help keep consistency across my projects.

Mobile and responsive targets are the primary concern. Consider an iPhone 16 Pro Max (430x932) to be the MAXIMUM work area. Consider an iPhone SE (375x667) to be the MINIMUM work area.

### Selections

Drop downs will be preferred for most items since there are a select few valid entries.

### Free Form User Configuration

Some items will need to have user added content. This will be such as device ids or phone numbers. These entries will need to have the ability to add a row, remove a row, or edit the value inside. All of them will require at least a single entry.

## Editable Configuration And Other Controls

These are the values that we will want to edit. Each item shuld have a tool tip and brief description.

### Device Type

Valid selections from a Select element (dropdown) are:

- MeshCore
- Meshtastic
- Sim800C
- Test

### UTC Offset

This will be a number selector. Valid options will be from -23 to 23. Options will be in half steps (0.5).

The interface will offer the user to type in a number, or to us UP/DOWN arrows.

When the user leaves the text box, the values will be normalized into the acceptable range.

### Oldest Message To Process

This is a value given in whole minutes.

It will be chosen from a dropdown / Select element.

Options are: 1, 5, 10, 15, 30, 45, 60

### Max Heater Time

This is a value given in whole minutes.

It will be chosen from a dropdown / Select element.

Options are: 15, 30, 60, 90, 120, 150, 180

### Heater Pin

This is a value set as an integer. It will refer to physical board pin.

It will be chosen from a dropdown / Select element.

Options are:

- 11/GPIO 17
- 13/GPIO 27
- 15/GPIO22
- 19/GPIO10
- 21/GPIO9
- 23/GPIO11
- 29/GPIO5
- 31/GPIO6
- 33/GPIO13
- 35/GPIO19
- 37/GPIO26
- 10/GPIO15
- 12/GPIO18
- 16/GPIO23
- 18/GPIO24
- 22/GPIO25
- 24/GPIO8
- 26/GPIO7
- 32/GPIO12
- 36/GPIO16
- 38/GPIO20
- 40/GPIO21

### MQ2

This is an enabled/off selector.

### Temperature Probe

This is an enabled/off selector.

### Light Sensor

This is an enabled/off selector.

If the light sensor is enabled, then three more settings become availble:

- HANGAR_DARK
  - Defaults to 20
  - Minimum is 0
  - Maximum is HANGAR_DIM
- HANGAR_DIM
  - Defaults to 60
  - Minumum is HANGAR_DIM
  - Maximum is HANGAR_LIT
- HANGAR_LIT
  - defaults to 90
  - Minimum is HANGAR_DIM
  - Maximum is 200

These values are whole number entries. Sliders or UP/DOWN arrows may be used.

### Display Enabled

This is an enabled/off selector.

### Test Mode

This is an enabled/off selector.

### Save

This will save any changes that the user has made. Changes are not automatically saved.

When the user elects to save changes, the user should be given an overview of the changes made and an offer to confirm or cancel the save operation.

### Reboot

This will reboot the HangarBuddy. If there are unsaved changes, it will alert the user and give the option to cancel.
