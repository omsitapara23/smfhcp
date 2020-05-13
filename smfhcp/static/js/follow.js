$(document).ready(function(){
    $(".followLink").click(function(event){
        event.preventDefault()
        $currentLink = $(this)
        $currentLink.addClass('active')
        var doctor_user_name = $currentLink.attr('href')

        if ($currentLink.children(".followDiv").children(".followImage").attr('src').endsWith('unfollow.png')) {
            $currentLink.children(".followDiv").children(".followImage").attr('src', "../static/images/follow.png")
            $currentLink.children(".followDiv").attr('title', 'Follow ' + doctor_user_name)
            followOrUnfollow("false", doctor_user_name)
        } else {
            $currentLink.children(".followDiv").children(".followImage").attr('src', "../static/images/unfollow.png")
            $currentLink.children(".followDiv").attr('title', 'Unfollow ' + doctor_user_name)
            followOrUnfollow("true", doctor_user_name)
        }

        $(".followLink").each(function(){
            if (!$(this).hasClass('active') && $(this).attr('href') == doctor_user_name) {
                if ($(this).children(".followDiv").children(".followImage").attr('src').endsWith('unfollow.png')) {
                    $(this).children(".followDiv").children(".followImage").attr('src', "../static/images/follow.png")
                    $(this).children(".followDiv").attr('title', 'Follow ' + doctor_user_name)
                } else {
                    $(this).children(".followDiv").children(".followImage").attr('src', "../static/images/unfollow.png")
                    $(this).children(".followDiv").attr('title', 'Unfollow ' + doctor_user_name)
                }
            }
        });
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