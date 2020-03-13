$(document).ready(function(){
    $("#followLink").click(function(event){
        event.preventDefault();
        var doctor_user_name = $("#followLink").attr('href')
        if ($("#followImage").attr('src').endsWith('unfollow.png')) {
            $("#followImage").attr('src', "../static/images/follow.png")
            $("#followDiv").attr('title', 'Follow ' + doctor_user_name)
            followOrUnfollow("false", doctor_user_name)
        } else {
            $("#followImage").attr('src', "../static/images/unfollow.png")
            $("#followDiv").attr('title', 'Unfollow ' + doctor_user_name)
            followOrUnfollow("true", doctor_user_name)
        }
    });
});

function followOrUnfollow(followFlag, doctor_user_name) {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    $.ajax({
            url : "/follow_or_unfollow/",
            type : "POST",
            data : { follow : followFlag, doctor_name : doctor_user_name},
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success : function(json) {
                console.log("success")
            },
            error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
}