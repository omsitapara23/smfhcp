var currentId;
var chatBox;
Talk.ready.then(function() {
    getUserAndFollowList(function(currentUser, followList) {
        console.log(currentUser, followList)
        window.me = new Talk.User({
            id: currentUser.id,
            name: currentUser.name
        });
        window.talkSession = new Talk.Session({
            appId: "tlFjwhc6",
            me: me
        });
        chatBox = talkSession.createChatbox();
        var convId;
        var conversation;
        for (var i of followList) {
            console.log(i)
            var other = new Talk.User({
                id: i.id,
                name: i.name
            });
            conversation = talkSession.getOrCreateConversation(Talk.oneOnOneId(me, other));
            conversation.setParticipant(me);
            conversation.setParticipant(other);
            currentId = i.id;
            $("#followList").append("<button name=\"follow_list_item\" id=\"" + i.id + "\" type=\"button\" class=\"list-group-item list-group-item-action follow-list\">" + i.id + "</button>")
        }
        chatBox.select(conversation)
        $("#" + currentId).addClass("active")
        chatBox.mount(document.getElementById("talkjs-container"));
    })
});

function getUserAndFollowList(callback) {
    $.ajax({
        url : "/get_follow_list/",
        type : "GET",
        success : function(json) {
            callback(json.me, json.follow_list);
        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

$(document).on('click', 'button[name="follow_list_item"]', function(event){
    console.log("here");
    event.preventDefault();
    var otherId = $(this).attr('id');
    var other = new Talk.User({
        id: otherId,
        name: otherId
    });
    $("#" + currentId).removeClass("active");
    currentId = otherId;
    $("#" + currentId).addClass("active");
    var conversation = talkSession.getOrCreateConversation(Talk.oneOnOneId(me, other));
    conversation.setParticipant(me);
    conversation.setParticipant(other);
    chatBox.select(conversation);
});
