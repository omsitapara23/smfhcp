$(document).ready(function(){
    $("#comment-form").on('submit', function(event){
        event.preventDefault();
        console.log("comment form submitted!")
        var user_name = $("#comment-form").attr('about').split("/")[0]
        var post_id = $("#comment-form").attr('about').split("/")[1]
        addComment(user_name, post_id)
    });
    $(document).on('click', 'a[name="replyButton"]', function() {
        event.preventDefault();
        var replyId = $(this).attr('href')
        if($("#reply" + replyId).css("display") == 'none') {
            $("#reply" + replyId).css("display", "block")
        } else {
            $("#reply" + replyId).css("display", "none")
        }
    });
    $(document).on('click', 'button[name="submitReplyButton"]', function(event){
        event.preventDefault();
        addReply($("#reply-form" + $(this).attr('about')).attr('about').split("/")[0], $("#reply-form" + $(this).attr('about')).attr('about').split("/")[1],
                $(this).attr('about'), $("#replyText" + $(this).attr('about')).val());
    });
});

function addComment(user_name, post_id){
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    $.ajax({
        url : "/add_comment/",
        type : "POST",
        data : { user_name : user_name, post_id : post_id, comment_text: $("#commentText").val()},
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
        success : function(json) {
            $("#showCommentsWrapper").prepend("<div style=\"margin-bottom: 20px;\" id=" + json.comment_id + ">" +
                    "<div style=\"margin-bottom: 10px; border: 1px solid #EAEAEA; border-radius: 4px;\">" +
                        "<div class=\"row\" style=\"background-color: #EAEAEA; padding: 10px; margin-left: 0px;margin-right: 0px;\">" +
                            "<div class=\"col-md-9\" align=\"left\" style=\"padding-left: 12px;\">" +
                               "<p style=\"margin-bottom: 0px; padding-left: 0px;\"><b>" + user_name +"</b></p>" +
                            "</div>" +
                            "<div class=\"col-md-3\" align=\"right\">" +
                                        "<a name=\"replyButton\" style=\"width: 14.45px;  display: inline-block;\" href=" + json.comment_id +" id=\"comment" + json.comment_id + "\">" +
                                            "<image src=\"/static/images/reply.svg\" style=\"width: 10px; float: left;\"></image>" +
                                       "</a>" +
                                        "<small class=\"text-muted\" style=\"padding-left: 5px; padding-right: 0px; margin-bottom: 0px;\">just now</small>" +
                            "</div>" +
                        "</div>" +
                        "<div style=\"padding: 10px; padding-left: 22px; padding-right: 22px; background-color: #F7F7F7;\">" +
                            "<p style=\"color: #495057; margin-bottom: 0px; white-space: pre-wrap;\">" + $("#commentText").val() + "</p>" +
                        "</div>" +
                    "</div>" +
                    "<div class=\"row justify-content-end\">" +
                        "<div class=\"col-md-11\" id=\"showReplyWrapper" + json.comment_id + "\">" +
                            "<div id=\"reply" + json.comment_id + "\" style=\"margin-top: 20px; display: none; margin-bottom: 10px;\">" +
                                "<form method=\"POST\" id=\"reply-form" + json.comment_id + "\" about=" + user_name + "/" + post_id + ">" +
                                    "<div class=\"form-row\">" +
                                   " <div class=\"form-group  col-md-9\">" +
                                        "<textarea name=\"replyText\" class=\"form-control\" id=\"replyText" + json.comment_id + "\" rows=\"2\" required placeholder=\"Add a reply...\"></textarea>" +
                                    "</div>" +
                                   " <div class=\"form-group col-md-3\">" +
                                      "  <button type=\"submit\" name=\"submitReplyButton\" about="+ json.comment_id + " id=\"addReplyButton" + json.comment_id + "\" class=\"btn btn-success btn-block\" style=\"padding-top: 9px; padding-bottom: 9px; background-color: #3ecb87; border: none; margin-top: 10px; border-radius: 20px !important; max-width: 150px;\">Post reply</button>" +
                                    "</div>" +
                                    "</div>" +
                                "</form>" +
                            "</div>" +
                        "</div>" +
                    "</div>" +
                    "</div>");
            $("#commentText").val('');
            console.log("success")
        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

function addReply(user_name, post_id, comment_id, replyText){
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    console.log(user_name, post_id, comment_id, replyText)
    $.ajax({
        url : "/add_reply/",
        type : "POST",
        data : { user_name : user_name, post_id : post_id, reply_text: replyText, comment_id : comment_id},
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
        success : function(json) {
            $("#replyText" + comment_id).val('')
            $("#reply" + comment_id).css("display", "none")
            $("#showReplyWrapper" + comment_id).append("<div style=\"margin-bottom: 10px; border: 1px solid #EAEAEA; border-radius: 4px; \">" +
                                "<div class=\"row\" style=\"background-color: #EAEAEA; padding: 10px; margin-left: 0px;margin-right: 0px;\">" +
                                    "<div class=\"col-md-8\" align=\"left\" style=\"padding-left: 12px;\">" +
                                        "<p style=\"margin-bottom: 0px; padding-left: 0px;\"><b>" + user_name + "</b></p>" +
                                    "</div>" +
                                    "<div class=\"col-md-4\" align=\"right\" style=\"padding-right: 12px;\">" +
                                        "<small class=\"text-muted\" style=\"padding-right: 0px; margin-bottom: 0px;\">just now</small>" +
                                    "</div>" +
                                "</div>" +
                                "<div style=\"padding: 10px; padding-left: 22px; padding-right: 22px; background-color: #F7F7F7;\">" +
                                    "<p style=\"color: #495057; margin-bottom: 0px; white-space: pre-wrap;\">" + replyText + "</p>" +
                                "</div>" +
                            "</div>");
            console.log("success")
        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}
