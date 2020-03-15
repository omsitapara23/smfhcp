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
                        "<div class=\"row\" style=\"background-color: #EAEAEA; margin-left: 0px;margin-right: 0px;\">" +
                            "<div class=\"col-md-9\" align=\"left\" style=\"padding-left: 12px;\">" +
                               "<p style=\"margin-bottom: 0px; padding-left: 0px;\"><b>" + user_name +"</b></p>" +
                            "</div>" +
                            "<div class=\"col-md-3\">" +
                                "<div class=\"row\">" +
                                    "<div class=\"col-md-5\" align=\"right\" style=\"padding-left: 12px; padding-right: 0px;\">" +
                                        "<a name=\"replyButton\" href=" + json.comment_id +" id=\"comment" + json.comment_id + "\">" +
                                            "<image src=\"/static/images/reply.svg\" style=\"width: 10px;\"></image>" +
                                       "</a>" +
                                    "</div>" +
                                    "<div class=\"col-md-7\" align=\"right\" style=\"padding-right: 12px; padding-left: 0px;\">" +
                                        "<small class=\"text-muted\" style=\"padding-right: 0px; margin-bottom: 0px;\">just now</small>" +
                                    "</div>" +
                                "</div>" +
                            "</div>" +
                        "</div>" +
                        "<div style=\"padding: .375rem .75rem; background-color: #F7F7F7;\">" +
                            "<p style=\"color: #495057; margin-bottom: 0px; white-space: pre-wrap;\">" + $("#commentText").val() + "</p>" +
                        "</div>" +
                    "</div>" +
                    "<div class=\"row justify-content-end\">" +
                        "<div class=\"col-md-11\" id=\"showReplyWrapper" + json.comment_id + "\">" +
                            "<div id=\"reply" + json.comment_id + "\" style=\"display: none; margin-bottom: 10px;\">" +
                                "<form method=\"POST\" id=\"reply-form" + json.comment_id + "\" about=" + user_name + "/" + post_id + ">" +
                                   " <div class=\"form-group\" style=\"margin-left: 0px; margin-right: 0px; margin-bottom: 5px;\">" +
                                        "<label for=\"replyText" + json.comment_id + "\">Add a reply</label>" +
                                        "<textarea name=\"replyText\" class=\"form-control\" id=\"replyText" + json.comment_id + "\" rows=\"2\" required></textarea>" +
                                    "</div>" +
                                   " <div align=\"right\">" +
                                      "  <button type=\"submit\" name=\"submitReplyButton\" about="+ json.comment_id + " id=\"addReplyButton" + json.comment_id + "\" class=\"btn btn-success btn-block\" style=\"padding-top: 9px; padding-bottom: 9px; background-color: #3ecb87; border: none; margin-top: 10px; border-radius: 20px !important; max-width: 150px;\">Post reply</button>" +
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
                                "<div class=\"row\" style=\"background-color: #EAEAEA; margin-left: 0px;margin-right: 0px;\">" +
                                    "<div class=\"col-md-8\" align=\"left\" style=\"padding-left: 12px;\">" +
                                        "<p style=\"margin-bottom: 0px; padding-left: 0px;\"><b>" + user_name + "</b></p>" +
                                    "</div>" +
                                    "<div class=\"col-md-4\" align=\"right\" style=\"padding-right: 12px;\">" +
                                        "<small class=\"text-muted\" style=\"padding-right: 0px; margin-bottom: 0px;\">just now</small>" +
                                    "</div>" +
                                "</div>" +
                                "<div style=\"padding: .375rem .75rem; background-color: #F7F7F7;\">" +
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
