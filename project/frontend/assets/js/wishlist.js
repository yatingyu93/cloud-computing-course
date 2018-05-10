function invoke_update_wl(attitude_sdk, uid, mid, wl) {
    return attitude_sdk.attitudebotPost({}, {
        'f': 'updatewl',
        'uid': uid,
        'mid': mid,
        'wl': wl
    }, {});
}

function update_wl(attitude_sdk, uid, mid, wl) {
    return invoke_update_wl(attitude_sdk, uid, mid, wl).then( function(response) {
        console.log(response.data);
        return response.data;
    });
}

function invoke_get_wishlist(sdk_wishlist, uid) {
    return sdk_wishlist.wishlistbotPost({}, {
        'f': 'get',
        'uid': uid
    }, {});
}

function get_wishlist(sdk_wishlist, uid) {
    return invoke_get_wishlist(sdk_wishlist, uid).then( function(response) {
        console.log(response.data);
        return response.data;
    });
}

function invoke_deletefrom_wishlist(sdk_wishlist, uid, mid) {
    return sdk_wishlist.wishlistbotPost({}, {
        'f': 'delete',
        'uid': uid,
        'mid': mid
    }, {});
}
function delete_from_wishlist(wishlist_sdk, uid, mid) {
    return invoke_deletefrom_wishlist(wishlist_sdk, uid, mid).then( function(response) {
        console.log(response.data);
        return response.data;
    });
}


/*------------------------- ---Initial--------------------------------*/
var pre_url = "./home.html?mid="
var cur = 0;
/*-----------------------------Script---------------------------------*/
$(document).ready(function(){

    var sdk_wishlist = {};
    var attitude_sdk = {};
    AWS.config.region = 'us-east-1';
    AmazonCognitoIdentity.region = 'us-east-1';
    var poolData = {
        UserPoolId: 'us-east-1_jDv7ZZJB9',
        ClientId: '2najgqvdlpscumkfl2r5smpi3k'
    };
    var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
    var logout_url = "https://cc-pj-domain.auth.us-east-1.amazoncognito.com/logout?client_id=2najgqvdlpscumkfl2r5smpi3k&logout_uri=https://s3.amazonaws.com/cloud-computing-project-bucket/frontend/index.html";
    $("#logout").attr('href', logout_url);
    var cognitoUser = userPool.getCurrentUser();

    if (cognitoUser != null) {
        cognitoUser.getSession(function (err, session) {
            if (err) {
                alert(err);
                return;
            }
            console.log(session);
            cognitoUser.getUserAttributes(function(err, result) {
                if (err) {
                    alert(err);
                    return;
                }
                for (var i = 0; i < result.length; i++) {
                    if (result[i].getName() == 'email') {
                        console.log(result[i].getValue());
                    }
                }
            });

            console.log('session validity: ' + session.isValid());
            sdk_wishlist = apigClientFactoryW.newClient();
            attitude_sdk = apigClientFactoryA.newClient();
        });
    } else {
        alert("login please");
        window.location = "./index.html";
    }
    $("#logout").click(function () {
        cognitoUser.signOut();
    });

    /*-------------------------------Data----------------------------------*/
    // wishlist api
    var wishlist = [];
    var wlres = get_wishlist(sdk_wishlist, cognitoUser.getUsername());
    var mid=[], title=[], poster=[], rating=[], release_date=[], overview=[], genres=[];
    var msize = 0;
    // Wait for search promise to finish
    $.when(wlres).done(function (rsp) {
        $('#loading').hide();
        $('.container').show();
        msize = rsp.length;
        console.log(msize);
        console.log('data loaded: ' + msize);
        wishlist = rsp;
        for (var i = 0; i < msize; i++) {
            mid.push(rsp[i]['mid']);
            title.push(rsp[i]['title']);
            poster.push(rsp[i]['poster']);
            rating.push(rsp[i]['rating']);
            release_date.push(rsp[i]['release_date']);
            var ov = rsp[i]['overview'];
            if (ov.length == 0)
                overview.push('......');
            else
                overview.push(rsp[i]['overview']);
            genres.push(rsp[i]['genres']);
        }

        appendBlock(cur,4, msize, mid, poster, title, release_date, rating, genres, overview);
        cur += 4;
    });

    $(window).scroll(function(event){
        if($(window).scrollTop() + $(window).height() >= $(document).height()) {
            appendBlock(cur,2, msize, mid, poster, title, release_date, rating, genres, overview);
            cur = Math.min(cur+2, msize)
        }
    });
    $("body").on('click','.remove-btn',function(){
        var v_btid = this.id;
        var cur_mid = v_btid.substring(4,v_btid.length);
        var target = "#wl-"+cur_mid;

        console.log(cur_mid);
        /* delete mid=cur_mid from current user's wishlist */
        delete_from_wishlist(sdk_wishlist, cognitoUser.getUsername(), cur_mid);
        update_wl(attitude_sdk, cognitoUser.getUsername(), cur_mid, 0);

        $(target).remove();
        appendBlock(cur,1, msize, mid, poster, title, release_date, rating, genres, overview);
        cur = Math.min(cur+1, msize)
    });
});


function appendBlock(offset,n, msize, mid, poster, title, release_date, rating, genres, overview){
  var i = 0;
  while(i < n && offset + i < msize) {
    var year = "????";
    if(release_date[offset+i] != null) year = release_date[offset+i].substring(0,4);
      var newblock = "<div class='wishlist-wrapper' id='wl-"+mid[offset+i]+
          "'><div class='wishlist-block'><div class='image-wrapper'><img class='img-wishlist' src='"+poster[offset+i]+
          "'></div><div><div class='wishlist-detail'><div class='wltitle' title='"+title[offset+i]+"'><h4>" +
          "<a href='"+pre_url+mid[offset+i]+"'>"+title[offset+i]+" ("+year+
          ")</a></h4></div><div class='wldetail'><span>Rating: </span><strong>"+rating[offset+i]+
          "</strong></div><div class='wldetail wlgenre'><span>Genres: </span>"+genres[offset+i]+
          "</div><div class='wldetail'><span>Overview: </span>"+overview[offset+i]+
          "</div><span class='remove-btn' id='btn-"+mid[offset+i]+"'>Remove from wishlist</span></div></div></div></div>";
      $(".wishlist-row").append(newblock);
      i += 1;
  }
}
