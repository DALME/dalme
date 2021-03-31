"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _UniqueComponentId = _interopRequireDefault(require("../utils/UniqueComponentId"));

var _DomHandler = _interopRequireDefault(require("../utils/DomHandler"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function bindEvents(el) {
  var modifiers = el.$_ptooltipModifiers;

  if (modifiers.focus) {
    el.addEventListener('focus', onFocus);
    el.addEventListener('blur', onBlur);
  } else {
    el.addEventListener('mouseenter', onMouseEnter);
    el.addEventListener('mouseleave', onMouseLeave);
    el.addEventListener('click', onClick);
  }
}

function unbindEvents(el) {
  var modifiers = el.$_ptooltipModifiers;

  if (modifiers.focus) {
    el.removeEventListener('focus', onFocus);
    el.removeEventListener('blur', onBlur);
  } else {
    el.removeEventListener('mouseenter', onMouseEnter);
    el.removeEventListener('mouseleave', onMouseLeave);
    el.removeEventListener('click', onClick);
  }
}

function onMouseEnter(event) {
  show(event.currentTarget);
}

function onMouseLeave(event) {
  hide(event.currentTarget);
}

function onFocus(event) {
  show(event.currentTarget);
}

function onBlur(event) {
  hide(event.currentTarget);
}

function onClick(event) {
  hide(event.currentTarget);
}

function show(el) {
  if (!el.$_ptooltipValue) {
    return;
  }

  var tooltipElement = create(el);
  align(el);

  _DomHandler.default.fadeIn(tooltipElement, 250);

  tooltipElement.style.zIndex = ++_DomHandler.default.zindex;
  window.addEventListener('resize', function onWindowResize() {
    hide(el);
    this.removeEventListener('resize', onWindowResize);
  });
}

function hide(el) {
  remove(el);
}

function getTooltipElement(el) {
  return document.getElementById(el.$_ptooltipId);
}

function create(el) {
  var id = (0, _UniqueComponentId.default)() + '_tooltip';
  el.$_ptooltipId = id;
  var container = document.createElement('div');
  container.id = id;
  var tooltipArrow = document.createElement('div');
  tooltipArrow.className = 'p-tooltip-arrow';
  container.appendChild(tooltipArrow);
  var tooltipText = document.createElement('div');
  tooltipText.className = 'p-tooltip-text';
  tooltipText.innerHTML = el.$_ptooltipValue;
  container.appendChild(tooltipText);
  document.body.appendChild(container);
  container.style.display = 'inline-block';
  return container;
}

function remove(el) {
  if (el) {
    var tooltipElement = getTooltipElement(el);

    if (tooltipElement && tooltipElement.parentElement) {
      document.body.removeChild(tooltipElement);
    }

    el.$_ptooltipId = null;
  }
}

function align(el) {
  var modifiers = el.$_ptooltipModifiers;

  if (modifiers.top) {
    alignTop(el);

    if (isOutOfBounds(el)) {
      alignBottom(el);
    }
  } else if (modifiers.left) {
    alignLeft(el);

    if (isOutOfBounds(el)) {
      alignRight(el);

      if (isOutOfBounds(el)) {
        alignTop(el);

        if (isOutOfBounds(el)) {
          alignBottom(el);
        }
      }
    }
  } else if (modifiers.bottom) {
    alignBottom(el);

    if (isOutOfBounds(el)) {
      alignTop(el);
    }
  } else {
    alignRight(el);

    if (isOutOfBounds(el)) {
      alignLeft(el);

      if (isOutOfBounds(el)) {
        alignTop(el);

        if (isOutOfBounds(el)) {
          alignBottom(el);
        }
      }
    }
  }
}

function getHostOffset(el) {
  var offset = el.getBoundingClientRect();

  var targetLeft = offset.left + _DomHandler.default.getWindowScrollLeft();

  var targetTop = offset.top + _DomHandler.default.getWindowScrollTop();

  return {
    left: targetLeft,
    top: targetTop
  };
}

function alignRight(el) {
  preAlign(el, 'right');
  var tooltipElement = getTooltipElement(el);
  var hostOffset = getHostOffset(el);

  var left = hostOffset.left + _DomHandler.default.getOuterWidth(el);

  var top = hostOffset.top + (_DomHandler.default.getOuterHeight(el) - _DomHandler.default.getOuterHeight(tooltipElement)) / 2;
  tooltipElement.style.left = left + 'px';
  tooltipElement.style.top = top + 'px';
}

function alignLeft(el) {
  preAlign(el, 'left');
  var tooltipElement = getTooltipElement(el);
  var hostOffset = getHostOffset(el);

  var left = hostOffset.left - _DomHandler.default.getOuterWidth(tooltipElement);

  var top = hostOffset.top + (_DomHandler.default.getOuterHeight(el) - _DomHandler.default.getOuterHeight(tooltipElement)) / 2;
  tooltipElement.style.left = left + 'px';
  tooltipElement.style.top = top + 'px';
}

function alignTop(el) {
  preAlign(el, 'top');
  var tooltipElement = getTooltipElement(el);
  var hostOffset = getHostOffset(el);
  var left = hostOffset.left + (_DomHandler.default.getOuterWidth(el) - _DomHandler.default.getOuterWidth(tooltipElement)) / 2;

  var top = hostOffset.top - _DomHandler.default.getOuterHeight(tooltipElement);

  tooltipElement.style.left = left + 'px';
  tooltipElement.style.top = top + 'px';
}

function alignBottom(el) {
  preAlign(el, 'bottom');
  var tooltipElement = getTooltipElement(el);
  var hostOffset = getHostOffset(el);
  var left = hostOffset.left + (_DomHandler.default.getOuterWidth(el) - _DomHandler.default.getOuterWidth(tooltipElement)) / 2;

  var top = hostOffset.top + _DomHandler.default.getOuterHeight(el);

  tooltipElement.style.left = left + 'px';
  tooltipElement.style.top = top + 'px';
}

function preAlign(el, position) {
  var tooltipElement = getTooltipElement(el);
  tooltipElement.style.left = -999 + 'px';
  tooltipElement.style.top = -999 + 'px';
  tooltipElement.className = 'p-tooltip p-component p-tooltip-' + position;
}

function isOutOfBounds(el) {
  var tooltipElement = getTooltipElement(el);
  var offset = tooltipElement.getBoundingClientRect();
  var targetTop = offset.top;
  var targetLeft = offset.left;

  var width = _DomHandler.default.getOuterWidth(tooltipElement);

  var height = _DomHandler.default.getOuterHeight(tooltipElement);

  var viewport = _DomHandler.default.getViewport();

  return targetLeft + width > viewport.width || targetLeft < 0 || targetTop < 0 || targetTop + height > viewport.height;
}

var Tooltip = {
  bind: function bind(el, options) {
    el.$_ptooltipModifiers = options.modifiers;
    el.$_ptooltipValue = options.value;
    bindEvents(el);
  },
  unbind: function unbind(el) {
    remove(el);
    unbindEvents(el);
  },
  update: function update(el, options) {
    el.$_ptooltipModifiers = options.modifiers;
    el.$_ptooltipValue = options.value;
  }
};
var _default = Tooltip;
exports.default = _default;
