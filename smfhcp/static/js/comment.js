$(document).ready(function(){
    $("#comment-form").on('submit', function(event){
        event.preventDefault();
        console.log("comment form submitted!")
        var user_name = $("#comment-form").attr('about').split("/")[0]
        var post_id = $("#comment-form").attr('about').split("/")[1]
        addComment(user_name, post_id)
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
            $("#showCommentsWrapper").prepend("<div style=\"margin-bottom: 10px;\">" +
                        "<p style=\"margin-bottom: 0px;\"><b>" + user_name + "</b></p>" +
                        "<div style=\"border: 0px solid #ced4da; border-radius: .25rem; padding: .375rem .75rem; background-color: #F7F7F7;\">" +
                            "<p style=\"color: #495057; margin-bottom: 0px;\">" + $("#commentText").val() + "</p>" +
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
