$(document).ready(function() {
    var $messages = $('.messages');
    var date;
    $messages.scrollTop($messages[0].scrollHeight);
    addResponse('Hello, how may I help?');

    function setCurTime() {
        date = new Date();
        var m = (date.getMinutes()<10?'0':'') + date.getMinutes();
        $('<div class="timestamp">' + date.getHours() + ':' + m + '</div>').appendTo($('.chatbox:last'));
    }

    function invokeChatbotApi(inputText) {
        return sdk.chatbotPost({}, inputText, {});
    }

    function sendMessage() {
        msg = $('#msginput').val();
        if ($.trim(msg) == '') {
            return false;
        }
        $('<div class="chatbox darker"><img src="./assets/img/img2.png" alt="Avatar" class="right">'+ msg +'</div>').appendTo($messages);
        setCurTime();
        $('#msginput').val(null);
        $messages.scrollTop($messages[0].scrollHeight);

        invokeChatbotApi(msg).then( function(response) {
            console.log(response.data);
            var data = response.data;
            rsp = data['message'];
            if (rsp && rsp.length > 0) {
                addResponse(rsp);
            } else {
                addResponse('Something went wrong. Please try again.');
            }
        });
    }

    $(window).on('keydown', function(e) {
        if (e.which == 13) {
            sendMessage();
            return false;
        }
    })

    $('#msgsubmit').click(function() {
        sendMessage();
    });

    function addResponse(content) {
        setTimeout(function() {
            $('<div class="chatbox left"><img src="./assets/img/img1.png" alt="Avatar"/>'+ content + '</div>').appendTo($messages);
            setCurTime();
            $messages.scrollTop($messages[0].scrollHeight);
        }, 200);
    }
});