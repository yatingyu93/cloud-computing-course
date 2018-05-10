function invoke_get_attitude(attitude_sdk, uid, mid) {
    return attitude_sdk.attitudebotPost({}, {
        'f': 'get',
        'uid': uid,
        'mid': mid
    }, {});
}

function get_attitude(attitude_sdk, uid, mid) {
    return invoke_get_attitude(attitude_sdk, uid, mid).then( function(response) {
        console.log(response.data);
        return response.data;
    });
}

function invoke_create_attitude(attitude_sdk, uid, mid) {
    return attitude_sdk.attitudebotPost({}, {
        'f': 'create',
        'uid': uid,
        'mid': mid
    }, {});
}

function create_attitude(attitude_sdk, uid, mid) {
    return invoke_create_attitude(attitude_sdk, uid, mid).then( function(response) {
        return response.data;
    });
}

function invoke_update_ld(attitude_sdk, uid, mid, ld) {
    return attitude_sdk.attitudebotPost({}, {
        'f': 'updateld',
        'uid': uid,
        'mid': mid,
        'ld': ld
    }, {});
}

function update_ld(attitude_sdk, uid, mid, ld) {
    return invoke_update_ld(attitude_sdk, uid, mid, ld).then( function(response) {
        console.log(response.data);
        return response.data;
    });
}

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

function invoke_create_wishlistitem(wishlist_sdk, uid) {
    return wishlist_sdk.wishlistbotPost({}, {
        'f': 'create',
        'uid': uid
    }, {});
}

function create_wishlistitem(wishlist_sdk, uid) {
    return invoke_create_wishlistitem(wishlist_sdk, uid).then( function(response) {
        return response.data;
    });
}

function invoke_addto_wishlist(wishlist_sdk, uid, mid) {
    return wishlist_sdk.wishlistbotPost({}, {
        "f": 'add',
        "uid": uid,
        "mid": mid
    }, {});
}

function add_to_wishlist(wishlist_sdk, uid, mid) {
    console.log(typeof mid);
    return invoke_addto_wishlist(wishlist_sdk, uid, mid).then( function(response) {
        console.log(response.data);
        return response.data;
    });
}

function invoke_deletefrom_wishlist(wishlist_sdk, uid, mid) {
    return wishlist_sdk.wishlistbotPost({}, {
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

function invoke_recommendations(movie_sdk, uid, indices, n, offset) {
    return movie_sdk.moviebotPost({}, {
        "f": "getrecommendations",
        "uid": uid,
        "indices": indices,
        "n": n,
        "offset": offset
    }, {});
}

function get_recommendations(movie_sdk, uid, indices, n, offset) {
    return invoke_recommendations(movie_sdk, uid, indices, n, offset).then( function(response) {
        var data = response.data;
        // console.log(data);
        return data;
    });
}

function invoke_moviedetail(movie_sdk, mid) {
    return movie_sdk.moviebotPost({}, {
        "f": "getmoviedetail",
        "mid": mid
    }, {});
}

function get_movie_detail(movie_sdk, mid) {
    return invoke_moviedetail(movie_sdk, mid).then( function(response) {
        // console.log(response.data);
        return response.data;
    });
}

function invoke_create_recommendation(movie_sdk, uid) {
    return movie_sdk.moviebotPost({}, {
        "f": "create",
        "uid": uid
    }, {});
}

function create_recommendation(movie_sdk, uid) {
    return invoke_create_recommendation(movie_sdk, uid).then( function(response) {
        return response.data;
    });
}

function add_response(content) {
    var mid = content['mid'];
    var title = content['title'];
    var poster = content['poster'];
    var rating = content['rating'];
    $("<li class=\"item\" id=\""+mid+"\"><img src=\""+poster+"\"><span class=\"text-content\"><span>"
        +title+"</span></span></li>").appendTo($('#itemlist'));
}

function change_detail(content) {
    var mid = content['mid'];
    var title = content['title'];
    var poster = content['poster']
    var overview = content['overview'];
    if (overview.length == 0)
        overview = '......';
    var rating = content['rating'];
    var genres = content['genres'];
    var release_date = content['release_date'];
    $('#movieid').text(mid);
    $('#movie_name').text(title);
    $('#movie_score').text(rating);
    $('#score_right').text("/10");
    $('#movie_genre').text(genres);
    $('#movie_date').text(release_date);
    $('#movie_overview').text(overview);
    $('#movie_img').attr('src', poster);
}


function show_attitude(attitude_sdk, uid, mid) {
    var getatt = get_attitude(attitude_sdk, uid, mid);
    $.when(getatt).done(function (rsp) {
        console.log('getatt' + rsp);
        var ld = rsp[0];
        var wl = rsp[1];
        console.log('ld: ' + ld + ', wl: ' + wl);
        if (ld == 0) {
            $('#like i').removeClass('fa-thumbs-up');
            $('#dislike i').removeClass('fa-thumbs-down');
            $('#like i').addClass('fa-thumbs-o-up');
            $('#dislike i').addClass('fa-thumbs-o-down');
        } else if (ld == -1) {
            $('#like i').removeClass('fa-thumbs-up');
            $('#dislike i').removeClass('fa-thumbs-o-down');
            $('#like i').addClass('fa-thumbs-o-up');
            $('#dislike i').addClass('fa-thumbs-down');
        } else if (ld == 1) {
            $('#like i').removeClass('fa-thumbs-o-up');
            $('#dislike i').removeClass('fa-thumbs-down');
            $('#like i').addClass('fa-thumbs-up');
            $('#dislike i').addClass('fa-thumbs-o-down');
        }

        if (wl == 0) {
            $('#wishlist i').removeClass('fa-minus-square');
            $('#wishlist i').addClass('fa-plus-square');
            $('#wltip').text('Add to wishlist');
        } else {
            $('#wishlist i').removeClass('fa-plus-square');
            $('#wishlist i').addClass('fa-minus-square');
            $('#wltip').text('Remove from wishlist');
        }
    });
}

$(document).ready(function () {

    $('.iconspan').hover(function () {
        $('.tooltiptext').show();
    });

    var movielist = [];
    var movie_sdk = {};
    var attitude_sdk = {};
    var wishlist_sdk = {};

    var url = new URL(window.location.href);
    var url_movie_id = url.searchParams.get("mid");

    console.log('url: ' + url_movie_id);

    AWS.config.region = 'us-east-1';
    AmazonCognitoIdentity.region = 'us-east-1';
    var poolData = {
        UserPoolId: 'us-east-1_jDv7ZZJB9',
        ClientId: '2najgqvdlpscumkfl2r5smpi3k'
    };
    var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

    // var logout_url = './index.html';
    var logout_url = "https://cc-pj-domain.auth.us-east-1.amazoncognito.com/logout?client_id=2najgqvdlpscumkfl2r5smpi3k&logout_uri=https://s3.amazonaws.com/cloud-computing-project-bucket/frontend/index.html";

    $("#logout").attr('href', logout_url);

    var cognitoUser = userPool.getCurrentUser();
    if (cognitoUser != null) {
        cognitoUser.getSession(function (err, session) {
            if (err) {
                alert(err);
                return;
            }
            cognitoUser.getUserAttributes(function(err, result) {
                if (err) {
                    alert(err);
                    return;
                }
                for (var i = 0; i < result.length; i++) {
                    if (result[i].getName() == 'email') {
                        console.log(result[i].getValue() + ', '+cognitoUser.getUsername());
                    }
                }
            });
            console.log('session validity: ' + session.isValid());

            movie_sdk = apigClientFactoryM.newClient();
            attitude_sdk = apigClientFactoryA.newClient();
            wishlist_sdk = apigClientFactoryW.newClient();
            var createwlres = create_wishlistitem(wishlist_sdk, cognitoUser.getUsername());
            $.when(createwlres).done(function (rsp) {
                console.log('createwl' + rsp);
            });
        });
    } else {
        alert("login please");
        window.location = "./index.html";
    }

    $('#like').click(function () {
        var cur_mid = $("#movieid").text();
        if ($('#like i').hasClass('fa-thumbs-o-up')) {
            $('#like i').removeClass('fa-thumbs-o-up');
            $('#like i').addClass('fa-thumbs-up');
            $('#dislike i').removeClass('fa-thumbs-down');
            $('#dislike i').addClass('fa-thumbs-o-down');
            update_ld(attitude_sdk, cognitoUser.getUsername(), cur_mid, 1);
        }
    });

    $('#dislike').click(function () {
        var cur_mid = $("#movieid").text();
        if ($('#dislike i').hasClass('fa-thumbs-o-down')) {
            $('#dislike i').removeClass('fa-thumbs-o-down');
            $('#dislike i').addClass('fa-thumbs-down');
            $('#like i').removeClass('fa-thumbs-up');
            $('#like i').addClass('fa-thumbs-o-up');
            //db dislike
            update_ld(attitude_sdk, cognitoUser.getUsername(), cur_mid, -1);
        }
    });

    $('#wishlist').click(function () {
        var cur_mid = $("#movieid").text();
        if ($('#wishlist i').hasClass('fa-plus-square')) {
            // not in wishlist now, add to wishlist
            var addwlres = add_to_wishlist(wishlist_sdk, cognitoUser.getUsername(), cur_mid);
            $.when(addwlres).done(function (rsp) {
                console.log('wl ' + rsp);
                update_wl(attitude_sdk, cognitoUser.getUsername(), cur_mid, 1);
                $('#wltip').text('Remove from wishlist');
            });
        } else {
            // in wishlist, remove from wishlist
            var delwlres = delete_from_wishlist(wishlist_sdk, cognitoUser.getUsername(), cur_mid);
            $.when(delwlres).done(function (rsp) {
                console.log('wl ' + rsp);
                update_wl(attitude_sdk, cognitoUser.getUsername(), cur_mid, 0);
                $('#wltip').text('Add to wishlist');
            });
        }
        $('#wishlist i').toggleClass('fa-plus-square');
        $('#wishlist i').toggleClass('fa-minus-square');
    });

    $("#logout").click(function () {
        cognitoUser.signOut();
    });

    $("#itemlist").delegate(".item", "click",function(){
        var mid = $(this).attr('id');
        console.log('click' + mid);
        for (var i = 0; i < movielist.length; i++) {
            var datamid = movielist[i]['mid'];
            if (datamid == mid) {
                change_detail(movielist[i]);
                var r = create_attitude(attitude_sdk, cognitoUser.getUsername(), mid);
                $.when(r).done(function () {
                    show_attitude(attitude_sdk, cognitoUser.getUsername(), mid);
                });
            }
        }
    });

    if (url_movie_id != null) {
        var res = get_movie_detail(movie_sdk, url_movie_id);
        $.when(res).done(function (content) {
            change_detail(content);
            console.log('url_movie_id change detail');
            var createattr = create_attitude(attitude_sdk, cognitoUser.getUsername(), url_movie_id);
            $.when(createattr).done(function () {
                show_attitude(attitude_sdk, cognitoUser.getUsername(), url_movie_id);
            });
        });
    }
    const all = 30;
    var idxList = [];
    for (var i = 0; i < all; i++) {idxList.push(i);}
    var randomIdxList = _.sample(idxList, idxList.length);
    console.log(randomIdxList);

    var cres = create_recommendation(movie_sdk, cognitoUser.getUsername());
    $.when(cres).done(function () {
        const n = 1;
        for (var idx = 0; idx < all/n; idx++) {
            var offset = idx * n;
            var queryres = get_recommendations(movie_sdk, cognitoUser.getUsername(), randomIdxList, n, offset);
            $.when(queryres).done(function(rsp) {
                movielist.push.apply(movielist, rsp);
                console.log(movielist.length);
                // movielist = rsp;
                console.log('data loaded: ' + rsp.length);
                for (var j = 0; j < rsp.length; j++) {
                    add_response(rsp[j]);
                }
                if (movielist.length == n && url_movie_id == null) {
                    change_detail(rsp[0]);
                    var createattr = create_attitude(attitude_sdk, cognitoUser.getUsername(), rsp[0]['mid']);
                    $.when(createattr).done(function () {
                        show_attitude(attitude_sdk, cognitoUser.getUsername(), rsp[0]['mid']);
                    });
                }
                if (movielist.length >= 3) {
                    $('#loading').hide();
                    $('.container').show();
                }
            });
        }
    });




});