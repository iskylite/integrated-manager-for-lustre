
/* http://snipplr.com/view/5945/ */
function formatNumber(number, decimals, dec_point, thousands_sep) {
    // http://kevin.vanzonneveld.net
    // +   original by: Jonas Raoni Soares Silva (http://www.jsfromhell.com)
    // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // +     bugfix by: Michael White (http://crestidg.com)
    // +     bugfix by: Benjamin Lupton
    // +     bugfix by: Allan Jensen (http://www.winternet.no)
    // +    revised by: Jonas Raoni Soares Silva (http://www.jsfromhell.com)    
    // *     example 1: number_format(1234.5678, 2, '.', '');
    // *     returns 1: 1234.57     
 
    var n = number, c = isNaN(decimals = Math.abs(decimals)) ? 2 : decimals;
    var d = dec_point == undefined ? "." : dec_point;
    var t = thousands_sep == undefined ? "," : thousands_sep, s = n < 0 ? "-" : "";
    var i = parseInt(n = Math.abs(+n || 0).toFixed(c)) + "", j = (j = i.length) > 3 ? j % 3 : 0;
 
    return s + (j ? i.substr(0, j) + t : "") + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + t) + (c ? d + Math.abs(n - i).toFixed(c).slice(2) : "");
}

/* http://snipplr.com/view/5949/ */
function formatBytes(bytes, decimals) {
  if (bytes == null || bytes == undefined) {
    return bytes;
  }

  if (decimals == undefined) {
    decimals = 2;
  }

	if (bytes >= 1073741824) {
	     bytes = formatNumber(bytes / 1073741824, decimals, '.', '') + 'GB';
	} else { 
		if (bytes >= 1048576) {
     		bytes = formatNumber(bytes / 1048576, decimals, '.', '') + 'MB';
   	} else { 
			if (bytes >= 1024) {
    		bytes = formatNumber(bytes / 1024, 0) + 'KB';
  		} else {
    		bytes = formatNumber(bytes, 0) + 'b';
			}
 		}
	}
  return bytes;
}

function formatBigNumber(number) {
  if (number == null || number == undefined) {
    return number;
  }

	if (number >= 1000000000) {
	     number = Math.floor(number / 1000000000) + 'B';
	} else { 
		if (number >= 1000000) {
     		number = Math.floor(number / 1000000) + 'M';
   	} else { 
			if (number >= 1000) {
    		number = Math.floor(number / 1000) + 'k';
  		}
 		}
	}
  return number;
}

/* https://docs.djangoproject.com/en/1.2/ref/contrib/csrf/#csrf-ajax */
$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

