/*
    This file was originally from:
        https://github.com/jokkebk/jgoboard
*/


// Import or create JGO namespace
var JGO = JGO || {};

JGO.BOARD = JGO.BOARD || {};

//var my_scale = 0.33
var my_scale = (0.5)


JGO.BOARD.small = {
    textures: {
        black: 'small/black.png',
        white: 'small/white.png',
        shadow:'small/shadow.png',
        board: 'small/shinkaya.jpg'
    },

    // Margins around the board, both on normal edges and clipped ones
    margin: {normal: 20 * my_scale, clipped: 20 * my_scale},

    // Shadow color, blur and offset
    boardShadow: {color: '#ffe0a8', blur: 15 * my_scale, offX: 2.5 * my_scale, offY: 2.5 * my_scale},

    // Lighter border around the board makes it more photorealistic
    border: {color: 'rgba(255, 255, 255, 0.3)', lineWidth: 2},

    // Amount of "extra wood" around the grid where stones lie
    padding: {normal: 10 * my_scale, clipped: 5 * my_scale},

    // Grid color and size, line widths
    grid: {color: '#202020', x: 25 * my_scale, y: 25 * my_scale, smooth: 0,
        borderWidth: 1.2, lineWidth: 0.9},

    // Star point radius
    stars: {radius: 5.0 * my_scale},

    // Coordinate color and font
    coordinates: {color: '#000000', font: 'normal 10px sanf-serif'},

    // Coordinate color and font
    title_font: {color: '#000000', font: 'bold 10px Freesans'},

    // Stone radius  and alpha for semi-transparent stones
    stone: {radius: 12 * my_scale, dimAlpha:0.6},

    // Shadow offset from center
    shadow: {xOff: -1, yOff: 1},

    // Mark base size and line width, color and font settings
    mark: {lineWidth: 1.0, blackColor: 'white', whiteColor: 'black',
        clearColor: 'black', font: 'bold 12px Freesans'}
};

JGO.BOARD.smallWalnut = JGO.util.extend(JGO.util.extend({}, JGO.BOARD.small), {
    textures: {board: 'small/walnut.jpg', shadow: 'small/shadow_dark.png'},
    boardShadow: {color: '#e2baa0'},
    grid: {color: '#101010', borderWidth: 1.4, lineWidth: 1.1}
});

JGO.BOARD.smallBW = JGO.util.extend(JGO.util.extend({}, JGO.BOARD.small), {
    textures: false, coordinates: {top: false, bottom: true, left: true, right: false}

});
