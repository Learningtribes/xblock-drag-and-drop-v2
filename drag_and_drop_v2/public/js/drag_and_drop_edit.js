async function DragAndDropEditBlock(runtime, element, params) {

    // Set up gettext in case it isn't available in the client runtime:
    if (typeof gettext == "undefined") {
        window.gettext = function gettext_stub(string) { return string; };
    }

    // Make gettext available in Handlebars templates
    Handlebars.registerHelper('i18n', function(str) { return gettext(str); });
    // Numeric rounding in Handlebars templates
    Handlebars.registerHelper('singleDecimalFloat', function(value) {
        if (value === "" || isNaN(Number(value))) {
            return "";
        }
        return Number(value).toFixed(Number(value) == parseInt(value) ? 0 : 1);
    });
    Handlebars.registerHelper('ifeq', function(v1, v2, options) {
      if (v1 === v2) {
        return options.fn(this);
      }
      return options.inverse(this);
    });

    var $element = $(element);

    const PYRAMID_TEMPLATE_TYPE = 0;
    const RECTANGLE_TEMPLATE_TYPE = 1;
    const BLANK_TEMPLATE_TYPE = 2;
    const CUSTOM_TEMPLATE_TYPE = 3;

    const ID_AUTHOR_CANVAS = '#id_author_canvas';
    const ID_PREVIEW_CANVAS = '#id_preview_canvas';

    var zones_tab_bk_image_width = 0;
    var zones_tab_bk_image_height = 0;

    var dragAndDrop = (function($) {
        var _fn = {
            build: {
                $el: {
                    feedback: {
                        form: $('.drag-builder .feedback-form', element),
                        tab: $('.drag-builder .feedback-tab', element)
                    },
                    backgroundChoose: {
                        templates: $('.drag-builder .supported-template-patterns', element),
                        tag: $('.drag-builder .background-image-tab', element),
                    },
                    zones: {
                        form: $('.drag-builder .zones-form', element),
                        tab: $('.drag-builder .zones-tab', element)
                    },
                    items: {
                        form: $('.drag-builder .items-form', element),
                        tab: $('.drag-builder .items-tab', element)
                    },
                    targetImage: $('.drag-builder .target .target-img', element),
                    zonesPreview: $('.drag-builder .target .zones-preview', element),
                },
                init: function() {
                    _fn.data = params.data;                             // The latest saved version of "Zones + Items" data different
                                                                        // with Editing version of them ( `_fn.build.form.zone.zoneObjects` + `_fn.build.form.item.itemObjects` )
                    _fn.selected_tab_id = undefined;
                    _fn.zone_tab_used_tpl_id = _fn.data.template_type;  // activated template id in Zone Tab
                    _fn.type_id = params.type_id;                       // selected template id in Background Tab
                    _fn.target_img_expanded_url = params.target_img_expanded_url;
                    _fn.custom_background = params.custom_background;   // uploaded custom background image
                    _fn.new_selected_tpl_data = undefined;              // new selected template sample data ( replaced duplicated data )
                    _fn.tpl_summaries = params.tpl_summaries;
                    _fn.is_old_version = params.is_old_version;
                    _fn.tabs_editing_status = {
                        '0': false,
                        '1': false,
                        '2': false,
                        '3': false
                    };

                    _fn.build.changeBackgroundSelect();

                    // Display target image
                    _fn.build.$el.targetImage.show();

                    _fn.build.refreshTabsStatus(init_flag=true);
                    _fn.build.clickHandlers();

                    // upload success handler
                    const rootDiv = document.getElementById('root');
                    rootDiv.addEventListener('uploadAssetsSuccessEvent', _fn.build.onBackgroundUploadSuccessHandler);
                    rootDiv.addEventListener('getAssetsSuccessEvent', _fn.build.onBackgroundGetAssetsSuccessHandler);

                    // Hide settings that are specific to assessment mode
                    _fn.build.$el.feedback.form.find('.problem-mode').trigger('change');

                    // Set focus on first input field.
                    $element.find('input:first').select();

                    // generate zoneObjects from data.zones
                    _fn.build.adjustDataScaleForOldVersion();
                    _fn.build.generateZoneObjectsFromZones();
                    // Create existing zones
                    _fn.build.recoverZonesFromZoneObjects();

                    if (LearningTribes && LearningTribes.QuestionMark) {
                        $wrappers = $('.drag-builder .tab .tab-content .question-mark-wrapper');
                        $wrappers.each(function(i, wrapper){
                            new LearningTribes.QuestionMark(wrapper);
                        });
                    };
                },
                getEditingStatus() {
                    /**
                     * Get editings status of all tags
                     * If at least one page is edited return true, otherwise return false
                     */
                    for (let i=0;i< 4;i++) {
                        if (_fn.tabs_editing_status[i.toString()] === true) {
                            return true
Ï                        }
                    }
                    return false
                },
                backgroundTemplateChoose: function(e) {
                    /**
                     * Handle select background
                     * Handle delete custom background, call background_check after deleted background
                     */
                    e.preventDefault();

                    if (e.target.matches('#item-delete-circle-3') || e.target.matches('#item-delete-circle-3 svg')) {
                        // delete custom background
                        runtime.notify('confirm', {
                            title: gettext('Delete the custom background?'),
                            message: gettext('Your current background will be deleted. Are you sure you want to continue?'),
                            actionLabel: gettext('Yes, delete the background'),
                            operation: function () {
                                const patternItemCustomBackground = $("#background-type-" + CUSTOM_TEMPLATE_TYPE.toString());
                                patternItemCustomBackground.css('display', 'none');

                                if (_fn.type_id !== CUSTOM_TEMPLATE_TYPE) {
                                    const oldAssetId = _fn.custom_background.substring(_fn.custom_background.lastIndexOf('/') + 1);
                                    if (oldAssetId) {
                                        _fn.build.form.background_check(oldAssetId, function(){
                                            _fn.custom_background = '';
                                            _fn.build.form.submit('1', continue_mode=true);
                                        });
                                    } else {
                                        _fn.custom_background = '';
                                        _fn.build.form.submit('1', continue_mode=true);
                                    }
                                }
                            },
                            onCancelCallback: function () {}
                        })
                    } else {
                        const type_id = parseInt(e.currentTarget.id.replace('background-type-', ''));
                        if (type_id !== CUSTOM_TEMPLATE_TYPE) {
                            _fn.build.changeBackgroundType(type_id);
                        } else if (_fn.custom_background) {
                            _fn.data.targetImg = _fn.custom_background;
                            _fn.build.changeBackgroundType(type_id);
                        }
                    }
                },
                changeBackgroundType: function(type_id, onConfirmHandler) {
                    /**
                     * Handle background change with confirmation check
                     * user select a different background
                     * custom background uploaded
                     */
                    if (type_id === undefined || type_id === _fn.type_id) {
                        if (type_id === CUSTOM_TEMPLATE_TYPE) {
                            _fn.build.changeBackgroundConfirmHandler(type_id, onConfirmHandler);
                        }
                        return;
                    }

                    if (_fn.type_id === BLANK_TEMPLATE_TYPE && type_id === CUSTOM_TEMPLATE_TYPE ||
                        _fn.type_id === CUSTOM_TEMPLATE_TYPE && type_id === BLANK_TEMPLATE_TYPE) {
                        // BLANK <=> CUSTOM keep zones with no confirmation
                        _fn.type_id = parseInt(type_id);
                        _fn.build.refreshTabsStatus();  // redraw tabs
                        _fn.build.updateSwitchers();

                        if (type_id === CUSTOM_TEMPLATE_TYPE) {
                            if (onConfirmHandler) {
                                onConfirmHandler.apply(this);
                            }
                        }

                        _fn.build.changeBackgroundSelect();

                    } else {
                        _fn.build.changeBackgroundConfirmHandler(type_id, onConfirmHandler);
                        // confirmation with zones will be deleted information
                        // runtime.notify('confirm', {
                        //     title: gettext('Change background?'),
                        //     message: gettext('The unused zones and answers will be deleted. Are you sure you want to continue?'),
                        //     actionLabel: gettext('Yes, delete the unused zones'),
                        //     operation: function () {
                        //         _fn.build.changeBackgroundConfirmHandler(type_id, onConfirmHandler);
                        //     },
                        //     onCancelCallback: function () {}
                        // })
                    }

                    _fn.build.set_tab_editing_status();
                    _fn.build.refresh_save_button_status();
                },
                generatePredefinedTemplateData: function(tpl_data) {
                    // May get duplicated zone_uid/zone_title and item_id/item_title while adding template sample data into editor
                    // So we have to convert these values into a new unique value as follow :
                    let used_zone_uid_convertor = {};

                    // Clone a new template sample data
                    _fn.new_selected_tpl_data = JSON.parse(JSON.stringify(tpl_data));

                    function generateDuplicatedTplZoneTitle(tpl_zone_title) {
                        // Generate New Template Zone name like `The Top Zone (2)` if `The Top Zone` already used
                        var count = 0;
                        var has_duplicated = false;

                        _fn.data.zones.forEach(function(zone) {
                            if (zone.title.includes(tpl_zone_title)) {
                                has_duplicated = true;
                                count++;
                            }
                        });

                        if (false === has_duplicated) {
                            return tpl_zone_title;
                        } else {
                            return tpl_zone_title + ' (' + (1 + count) + ')';
                        }
                    };

                    // Check duplicated zones in fields `zones` :
                    _fn.new_selected_tpl_data.zones.forEach(function(tpl_zone) {
                        // Assign new zone uids + titles for duplicated zones
                        _fn.data.zones.forEach(function(saved_zone) {
                            if (saved_zone.uid === tpl_zone.uid) {
                                let new_uid = _fn.build.form.zone.generateUID();

                                used_zone_uid_convertor[tpl_zone.uid] = new_uid;    // Saved mapping from old duplicated zone id ---> new zone id
                                tpl_zone.uid = new_uid;
                                if (tpl_zone.title === saved_zone.title) {
                                    tpl_zone.title = generateDuplicatedTplZoneTitle(tpl_zone.title);
                                }

                            }
                        });
                    });
                    // Check items :
                    let used_items_ids_set = new Set();

                    function generateDuplicatedTplItemTitle(tpl_item_display_name) {
                        // Generate New Template Item name like `Go to Middle Zone (2)` if `Go to Middle Zone` already used
                        var count = 0;
                        var has_duplicated = false;

                        _fn.data.items.forEach(function(item) {
                            if (item.displayName.includes(tpl_item_display_name)) {
                                has_duplicated = true;
                                count++;
                            }
                        });

                        if (false === has_duplicated) {
                            return tpl_item_display_name;
                        } else {
                            return tpl_item_display_name + ' (' + (1 + count) + ')';
                        }
                    };
                    // collecting used items ids.
                    _fn.data.items.forEach(function(saved_item) {
                        used_items_ids_set.add(saved_item.id);
                    });
                    for (var n = 0; n < _fn.new_selected_tpl_data.items.length; n++) {
                        // Check duplicated item_ids in field `items` :
                        for( var new_item_id = _fn.new_selected_tpl_data.items[n].id; true; new_item_id++) {
                            if (used_items_ids_set.has(new_item_id)) {
                                continue;
                            }
                            _fn.new_selected_tpl_data.items[n].id = new_item_id;
                            used_items_ids_set.add(new_item_id);
                            break;
                        }
                        let item_display_name = _fn.new_selected_tpl_data.items[n].displayName;
                        _fn.new_selected_tpl_data.items[n].displayName = generateDuplicatedTplItemTitle(item_display_name);

                        // Check duplicated Related zone UIDs in fields `items` :
                        for (var i = 0; i < _fn.new_selected_tpl_data.items[n].zones.length; i++) {
                            var related_zone_uid = _fn.new_selected_tpl_data.items[n].zones[i];
                            if (related_zone_uid in used_zone_uid_convertor) {
                                _fn.new_selected_tpl_data.items[n].zones[i] = used_zone_uid_convertor[related_zone_uid];    // replace related zone it of item with new value
                            }
                        };

                    };

                },
                changeBackgroundConfirmHandler(type_id, onConfirmHandler) {
                    /**
                     * Handle check zones usage with answers
                     * Clean zones canvas for render
                     * Check and delete unused custom background asset
                     *
                     */
                    // find used zones
                    var usedZones = [];
                    for (var itemIndex=0;itemIndex<_fn.data.items.length;itemIndex++) {
                        const currentItem = _fn.data.items[itemIndex];
                        usedZones = usedZones.concat(currentItem.zones);
                    }

                    // Coming from background/Zones page get zones and clean ZoneObjects
                    _fn.build.getZonesFromZoneObjects();
                    _fn.build.form.zone.zoneObjects = [];
                    $(ID_AUTHOR_CANVAS).empty();
                    if (type_id === BLANK_TEMPLATE_TYPE) {
                        $(ID_AUTHOR_CANVAS).css("background-image", "url()");
                        $(ID_PREVIEW_CANVAS).css("background-image", "url()");
                    }

                    if (usedZones.length > 0) {
                        if (type_id === BLANK_TEMPLATE_TYPE || type_id === CUSTOM_TEMPLATE_TYPE) {
                            // at least one zone is used, keep all zones
                        } else {
                            // delete all zones
                            _fn.data.zones = [];
                            _fn.data.items = [];
                        }
                    } else {
                        // on zone is used, delete zones
                        _fn.data.zones = [];
                    }

                    // set the new type_id
                    _fn.type_id = parseInt(type_id);
                    _fn.build.refreshTabsStatus();  // redraw tabs
                    _fn.build.updateSwitchers();

                    if (onConfirmHandler) {
                        // receive asset url from uploaded image asset detail
                        onConfirmHandler.apply(this);
                    }

                    _fn.build.changeBackgroundSelect();

                    // create zones from pyramid or rectangles template
                    params.predefined_templates.forEach(function(tpl_data) {
                        if (tpl_data.template_type === _fn.type_id) {
                            // generate predefined template data, we will add them into data after user select Zones Tab
                            _fn.build.generatePredefinedTemplateData(tpl_data);
                        }
                    });

                    return true;
                },
                changeBackgroundSelect() {
                    /**
                     * Changing the background based on user selection
                     * Checks for the type of template selected and updates the background image accordingly
                     */

                    if (_fn.type_id !== CUSTOM_TEMPLATE_TYPE) {
                        // PYRAMID RECTANGLE BLANK clean background image use template default background
                        _fn.data.targetImg = "";
                    }

                    if (_fn.custom_background) {
                        $('#id-background-thumbnail')
                            .css("background-image", "url('" + _fn.custom_background + "')");
                    }

                    // Handle the display of selected and delete circles
                    for (var i = 0; i < params.tpl_summaries.length; i++) {
                        const tpl_summary = params.tpl_summaries[i];
                        // Delete circle appears when the custom background is not selected
                        const selecedObj = $("#item-selected-circle-" + i.toString());
                        const deleteCircleObj = $("#item-delete-circle-" + i.toString());
                        if (parseInt(tpl_summary.type_id) === CUSTOM_TEMPLATE_TYPE && _fn.type_id !== CUSTOM_TEMPLATE_TYPE && _fn.custom_background) {
                            deleteCircleObj.css('display', '');
                        } else {
                            deleteCircleObj.css('display', 'none');
                        }

                        // Handle the display of selected circles
                        // Selected circle appears when the background is selected
                        if (_fn.type_id === parseInt(tpl_summary.type_id)) {
                            selecedObj.css('display', '');
                        } else {
                            selecedObj.css('display', 'none');
                        }
                    }

                    // Handle the display of custom background
                    const patternItemCustomBackground = $("#background-type-" + CUSTOM_TEMPLATE_TYPE.toString());
                    if (_fn.type_id !== CUSTOM_TEMPLATE_TYPE && !_fn.custom_background) {
                        patternItemCustomBackground.css('display', 'none');
                    } else {
                        patternItemCustomBackground.css('display', '')
                    }
                },
                onBackgroundUploadSuccessHandler(e) {
                    /**
                     * Handle the uploaded custom background
                     * Set the asset url to background and custom_background from uploaded image file
                     * Save xblock directly
                     */
                    // old asset to delete
                    const oldAssetId = _fn.data.targetImg.substring(_fn.data.targetImg.lastIndexOf('/') + 1);
                    const newXblockAsset = e.detail.asset;
                    const newBlockId = newXblockAsset.id.toString();

                    if (oldAssetId !== newBlockId) {
                        if (_fn.custom_background) {
                            // overwrites previously custom background
                            runtime.notify('confirm', {
                                title: gettext('Replace the custom background?'),
                                message: gettext('Your current background will be deleted and immediately replaced by the new upload. Are you sure you want to continue?'),
                                actionLabel: gettext('Yes, replace the background'),
                                operation: function () {
                                    onConfirmReplaceCustomBackgroundHandler();
                                }
                            });
                        } else {
                            onConfirmReplaceCustomBackgroundHandler();
                        }
                    }

                    function onConfirmReplaceCustomBackgroundHandler (){
                        if (oldAssetId) {
                            _fn.build.form.background_check(oldAssetId, function(){
                                onBGCheckCallback();
                            });
                        } else {
                            onBGCheckCallback();
                        }

                        function onBGCheckCallback() {
                            _fn.build.changeBackgroundType(CUSTOM_TEMPLATE_TYPE, function() {
                                _fn.data.targetImg = newXblockAsset.url;
                                _fn.custom_background = newXblockAsset.url;
                                _fn.build.form.submit('1', continue_mode=true);
                            })
                        }
                    }
                },
                onBackgroundGetAssetsSuccessHandler(e) {

                },
                updateSwitchers() {
                    /**
                     * Handle switcher display and default value
                     */
                    var switcherDisplayBorders =  $('#id_switcher_display_borders');
                    if (_fn.type_id === BLANK_TEMPLATE_TYPE) {
                        _fn.data.displayBorders = true;     // can't switch off
                        switcherDisplayBorders.addClass('hidden');
                    } else {
                        _fn.data.displayBorders = false;
                        switcherDisplayBorders.removeClass('hidden');
                        switcherDisplayBorders.css('display', 'flex');
                    }
                    _fn.data.displayLabels = true
                },

                validate: function(tabID) {
                    // validate user input argument while clicking button "save"
                    var success = true;

                    if (_fn.tabs_editing_status['0']) {
                        var display_name = $element.find('.display-name').val();
                        var weight = $element.find('.weight').val();

                        if (display_name === undefined || display_name === '' || weight === undefined) {
                            success = false;
                        }
                    } else if (_fn.tabs_editing_status['1']) {
                        if (_fn.type_id === undefined || _fn.type_id === null) {
                            success = false;
                        } else {
                            if (_fn.type_id === CUSTOM_TEMPLATE_TYPE && _fn.custom_background === undefined) {
                                success = false;
                            }
                        }
                    } else if (_fn.tabs_editing_status['2']) {
                        if (_fn.build.form.zone.zoneObjects.length === 0) {
                            success = false;
                        }
                    } else if (_fn.tabs_editing_status['3']) {
                        if (_fn.build.form.item.itemObjects.length === 0 || _fn.build.form.zone.zoneObjects.length === 0) {
                            success = false;
                        } else {
                            var zones_uids = new Set();
                            _fn.build.form.zone.zoneObjects.forEach(function(zone) {
                                zones_uids.add(zone.uid);
                            });
                            _fn.build.form.item.itemObjects.forEach(function(item) {
                                item.zones.forEach(function(zone_uid) {
                                    if (!zones_uids.has(zone_uid)) {
                                        success = false;
                                    }
                                });
                            })
                        }
                    }

                    if (!success) {
                        runtime.notify('error', {
                            'title': window.gettext('There was an error with your form.'),
                            'message': window.gettext('Please check over your submission.')
                        });
                    }
                    return success;
                },

                refreshTabsStatus: function(init_flag = false, selected_tab_id = undefined) {
                    $('.supported-setting-tags-nav > li').each( function (i, obj) {
                        var is_activated = obj.className.includes('active-section');

                        if ( obj.id === "2") {
                            // If var. `target_img_expanded_url` defined & type_id is null, that also means the data is Old version.
                            if ((_fn.type_id === undefined || _fn.type_id === null) && _fn.target_img_expanded_url === null) {
                                obj.className = 'nav-item disable-section';
                            } else {
                                obj.className = is_activated && (selected_tab_id!==undefined ? selected_tab_id === obj.id : true) ? 'nav-item active-section' : 'nav-item';
                            }
                        } else if (obj.id === "3") {
                            if (
                                // If var. `target_img_expanded_url` defined & type_id is null, that also means the data is Old version.
                                ((_fn.build.form.zone.zoneObjects === undefined || _fn.build.form.zone.zoneObjects.length === 0) && (_fn.data.zones === undefined || _fn.data.zones.length === 0))
                                || (_fn.type_id === null && _fn.target_img_expanded_url === null)
                            ) {
                                obj.className = 'nav-item disable-section';
                            } else {
                                obj.className = is_activated && (selected_tab_id!==undefined ? selected_tab_id === obj.id : true) ? 'nav-item active-section' : 'nav-item';
                            }

                            var readonlyBoxes = $('.readonly_zone_box');
                            if (_fn.data.displayBorders === true) {
                                readonlyBoxes.removeClass('no-border');
                            } else {
                                if (!readonlyBoxes.hasClass('no-border')) {
                                    readonlyBoxes.addClass('no-border');
                                }
                            }

                        } else {
                            if (init_flag === true && obj.id === "0") {
                                obj.className = 'nav-item active-section';
                            } else {
                                obj.className = is_activated && (selected_tab_id!==undefined ? selected_tab_id === obj.id : true) ? 'nav-item active-section' : 'nav-item';
                            }
                        }

                    } );
                },

                recoverZonesFromZoneObjects: function(id_zones_canvas=ID_AUTHOR_CANVAS) {
                    _fn.build.form.zone.zoneObjects.forEach(function(zoneObj) {
                        if (ID_AUTHOR_CANVAS === id_zones_canvas) {
                            // Create resizable zones on Author Canvas ( `ZoneTab` )
                            _fn.build.form.zone.makeResizableZone(zoneObj, id_zones_canvas);
                        } else {
                            // Create readonly zones on `AnswerTab`
                            _fn.build.form.zone.makeReadonlyZone(zoneObj, id_zones_canvas);
                        }
                    });

                    _fn.build.refreshTabsStatus();  // redraw tabs
                },

                refreshZonesSettings: function() {
                    var resizableBox = $('.resizable_box');
                    if (_fn.data.displayBorders === true) {
                        resizableBox.removeClass('no-border');
                    } else {
                        if (!resizableBox.hasClass('no-border')) {
                            resizableBox.addClass('no-border');
                        }
                    }

                    var zoneTitle = $('.zone_title');
                    if (_fn.data.displayLabels === true) {
                        if (zoneTitle.hasClass('hidden')) {
                            zoneTitle.removeClass('hidden');
                        }
                    } else {
                        if (!zoneTitle.hasClass('hidden')) {
                            zoneTitle.addClass('hidden');
                        }
                    }
                },
                renderTemplateZonesAreaBackgroud: function(canvas_element, tabId) {
                    let drawing_area_selector = '.zones-tab .tab-content .drag_drop_area';

                    // This method is used by ZoneTab & AnswerTab
                    canvas_element.empty(); // clean all element in the Canvas
                    // For AnswerTab, we have another named id set
                    if ('3' === tabId) {
                        drawing_area_selector = '.items-tab .tab-content .drag_drop_area';
                    }

                    // Whether new template has been selected OR AnswerTab selected :
                    if (_fn.type_id !== _fn.zone_tab_used_tpl_id || '3' === tabId || '2' === tabId) {
                        // Create new background
                        if (_fn.type_id === PYRAMID_TEMPLATE_TYPE || _fn.type_id === RECTANGLE_TEMPLATE_TYPE) {           // Triangle template and Two rectangle template
                            if (_fn.type_id === PYRAMID_TEMPLATE_TYPE) {
                                $(drawing_area_selector).css('height', '500px');
                            } else if (_fn.type_id === RECTANGLE_TEMPLATE_TYPE) {
                                $(drawing_area_selector).css('height', '500px');
                            }
                            _fn.tpl_summaries.forEach(function(tpl_summary) {
                                if (tpl_summary.type_id === parseInt(_fn.type_id)) {
                                    $(drawing_area_selector).css("background-image", "url(" + tpl_summary.thumbnail + ")");
                                }
                            });
                        } else if (_fn.type_id === 3 || (_fn.type_id === null && _fn.target_img_expanded_url != null) ) {     // Custom Background template
                            if (_fn.type_id === 3) {
                                $(drawing_area_selector)
                                    .css("background-image", "url(" + _fn.data.targetImg + ")");    // paste uploaded image into background
                            } else {
                                $(drawing_area_selector)
                                    .css("background-image", "url(" + _fn.target_img_expanded_url + ")");    // paste uploaded image into background
                            }
                            $(drawing_area_selector).css('max-height', '500px');
                        } else {
                            $(drawing_area_selector).css('height', '500px');
                        }
                    }

                },

                selectTabPage: function(tabId) {
                    var $tabPages = $(".supported-setting-tags section");
                    var pageFrame = $(".xblock--drag-and-drop--editor");
                    var canvas_element = $(ID_AUTHOR_CANVAS);
                    var preview_canvas_element = $(ID_PREVIEW_CANVAS);

                    if (tabId === _fn.selected_tab_id) {
                        return;     // Forbid multiple drawing on Tab
                    }

                    // We flush "zones/items" data from Cache( `...form.zone.ZoneObjects/item.itemObjects` ) to zone data holder( `_fn.data.zones/items` )
                    // If we switches Tabs between ( "Background / Zones / Answer Tabs" ). And render "Zones/Items" in each Tabs of them by calling
                    // methods : `generateZoneObjectsFromZones()` + `recoverZonesFromZoneObjects()` .
                    if (_fn.selected_tab_id !== "0") {
                        // don't get zones data from answers page, it doesn't change zones
                        if (_fn.selected_tab_id !== "3") {
                            // get zones from other page and clean ZoneObjects
                            _fn.build.getZonesFromZoneObjects();
                        }
                        _fn.build.form.zone.zoneObjects = [];
                        // get items from other page and clean ItemObjects
                        _fn.build.getItemsFromItemObjects();
                        _fn.build.form.item.itemObjects = [];

                        // Here, we clean zones areas in "Zone Tab" + "Answer Tab"
                        canvas_element.empty();
                        preview_canvas_element.empty();
                    }

                    // Update new selected template data into data ( `Zones` + `Answers` )
                    if (tabId === "2" || tabId === "3") {

                        // Apply data of new selected template of Background Tab
                        // &
                        // `new_selected_tpl_data` will also be applied when user clicking button `save` ( method submit() ) on Background Tab
                        if (_fn.new_selected_tpl_data !== undefined) {
                            _fn.data.zones = _fn.data.zones.concat(_fn.new_selected_tpl_data.zones);
                            _fn.data.items = _fn.data.items.concat(_fn.new_selected_tpl_data.items);
                            _fn.new_selected_tpl_data = undefined;
                        }
                    }

                    if ('1' === tabId) {    // Background Image tab
                        pageFrame.height('750px');

                        $('#id_xblock_save_button').className = 'action-item';

                    } else if ('2' === tabId) { // Zones design tab

                        if (_fn.type_id === PYRAMID_TEMPLATE_TYPE) {
                            canvas_element.css('height', '500px');
                        } else if (_fn.type_id === RECTANGLE_TEMPLATE_TYPE) {
                            canvas_element.css('height', '500px');
                        } else if (_fn.type_id === CUSTOM_TEMPLATE_TYPE) {
                            // for test image height
                            // var img = new Image();
                            // img.addEventListener("load", function() {
                            //     canvas_element.css('height', img.height + 'px');
                            // }, false);
                            // img.src = _fn.custom_background;
                            canvas_element.css('height', '500px');
                        } else {
                            canvas_element.css('height', '500px');
                        }

                        if (_fn.type_id === BLANK_TEMPLATE_TYPE) {
                            pageFrame.height('836px');
                        } else if (_fn.type_id === RECTANGLE_TEMPLATE_TYPE) {
                            pageFrame.height('886px');
                        } else {
                            pageFrame.height('896px');
                        }

                        _fn.build.renderTemplateZonesAreaBackgroud(canvas_element, tabId);

                        _fn.zone_tab_used_tpl_id = _fn.type_id;
                        // generate zoneObjects from data.zones
                        _fn.build.generateZoneObjectsFromZones();
                        // Create existing zones
                        _fn.build.recoverZonesFromZoneObjects();

                        if (LearningTribes && LearningTribes.Switcher) {
                            if (_fn.type_id === BLANK_TEMPLATE_TYPE) {
                                $('#id_switcher_display_borders').addClass('hidden');
                            } else {
                                var displayBordersSwitcher = $('#id_switcher_display_borders').find('.switcher')[0];
                                new LearningTribes.Switcher(displayBordersSwitcher, _fn.data.displayBorders, function(checked){
                                    _fn.data.displayBorders = checked
                                    _fn.build.refreshZonesSettings();
                                });
                            }
                            var displayLabelsSwitcher = $('#id_switcher_display_labels').find('.switcher')[0];
                            new LearningTribes.Switcher(displayLabelsSwitcher, _fn.data.displayLabels, function(checked){
                                _fn.data.displayLabels = checked
                                _fn.build.refreshZonesSettings();
                            });
                            _fn.build.refreshZonesSettings();
                        }

                    } else if ('3' === tabId) { // Item design tab
                        pageFrame.height('976px');

                        // Render Preview Background
                        _fn.build.renderTemplateZonesAreaBackgroud(preview_canvas_element, tabId);

                        // generate zoneObjects from data.zones
                        _fn.build.generateZoneObjectsFromZones();
                        // Create zones on AnswerTab
                        _fn.build.recoverZonesFromZoneObjects(ID_PREVIEW_CANVAS);

                        // Remove all existing Answer Cards
                        $('.answers_collection .answer_item').remove();
                        // Render existing Answers
                        _fn.build.form.item.itemObjects = _fn.data.items;
                        _fn.build.form.item.itemObjects.forEach(function(answer_obj) {
                            _fn.build.form.item.createAnswerItem(answer_obj, false);
                        });
                        // Rebind events to Answers Cards
                        _fn.build.rebind_events_for_answers_tab();

                    } else {
                        pageFrame.height('690px');
                        $('#id_xblock_save_button').className = 'action-item';
                    }

                    _fn.selected_tab_id = tabId;    // Assign current selected tab ID
                    _fn.build.refresh_save_button_status();

                    $tabPages.each(function () {
                        var pg = $(this);
                        if ( tabId === pg.attr('id') ) {
                            pg.removeClass('hidden');
                        } else {
                            if (!pg.hasClass('hidden')) {
                                pg.addClass('hidden');
                            }
                        }

                    })

                },

                adjustDataScaleForOldVersion() {
                    if (_fn.is_old_version === true) {
                        var imgRawWidth = zones_tab_bk_image_width;
                        var imgRawHeight = zones_tab_bk_image_height;
                        var imgRealWidth = 0;
                        var imgRealHeight = 0;

                        // Background Image real size calculation
                        if (imgRawWidth > $('#id_author_canvas').width()) {
                            var percent = $('#id_author_canvas').width() / imgRawWidth;
                            imgRealWidth = $('#id_author_canvas').width();
                            imgRealHeight = imgRawHeight * percent;
                        } else if (imgRawHeight > $('#id_author_canvas').height()) {
                            var percent = $('#id_author_canvas').height() / imgRawHeight;
                            imgRealHeight = $('#id_author_canvas').height();
                            imgRealWidth = imgRawWidth * percent;
                        }

                        if (imgRealWidth > $('#id_author_canvas').width()) {
                            var percent = $('#id_author_canvas').width() / imgRealWidth;
                            imgRealWidth = $('#id_author_canvas').width();
                            imgRealHeight = imgRealHeight * percent;
                        } else if (imgRealHeight > $('#id_author_canvas').height()) {
                            var percent = $('#id_author_canvas').height() / imgRealHeight;
                            imgRealHeight = $('#id_author_canvas').height();
                            imgRealWidth = imgRealWidth * percent;
                        }

                        _fn.data.zones.forEach(function(zone) {
                            var x_percent = imgRealWidth / imgRawWidth;
                            zone.x = x_percent * zone.x;
                            zone.width = x_percent * zone.width;
                            var y_percent = imgRealHeight / imgRawHeight;
                            zone.y = y_percent * zone.y;
                            zone.height = y_percent * zone.height;
                        });

                    }
                },

                generateZoneObjectsFromZones() {
                    /**
                     * Handle creating `ZoneObjects` from zones data if `ZoneObjects` is empty.
                     */
                    if (_fn.build.form.zone.zoneObjects.length === 0) {
                        // for empty zoneObjects, just to generate from zones data
                        _fn.data.zones.forEach(function(zone) {
                            _fn.build.form.zone.add({
                                uid: zone.uid,      // set `uid` field
                                title: zone.title,  // set `title` field
                                width: zone.width,
                                height: zone.height,
                                x: zone.x,
                                y: zone.y,
                                align: 'none'
                            });
                        });

                    }
                },

                getZonesFromZoneObjects() {
                    if (_fn.build.form.zone.zoneObjects.length > 0) {
                        _fn.data.zones = _fn.build.deepCopy(_fn.build.form.zone.zoneObjects);
                    }
                },

                getItemsFromItemObjects() {
                    if (_fn.build.form.item.itemObjects.length > 0) {
                        _fn.data.items = _fn.build.deepCopy(_fn.build.form.item.itemObjects);
                    }
                },

                /** Makes a deep copy of an array or object (mostly) */
                deepCopy(obj)
                {
                    if (typeof obj !== 'object' || obj === null)
                        return obj;
                    var cpy = Array.isArray(obj) ? [] : {};
                    for (var key in obj)
                        cpy[key] = _fn.build.deepCopy(obj[key]);
                    return cpy;
                },

                rebind_events_for_answers_tab: function() {
                    // For creating answer items dynamiclly, we rebind event for these new items.
                    var old_answer_text = undefined;

                    $('.answer_zones_dropdown_menu').bind('mouseover', function(e) {
                        if (e.currentTarget.classList.contains('fa-caret-down')) {
                            e.currentTarget.classList.remove('fa-caret-down');
                            e.currentTarget.classList.add('fa-caret-up');
                        }

                        let dropdown_content_elements = e.currentTarget.parentElement.getElementsByClassName('answer_zones_dropdown_content');

                        if (dropdown_content_elements.length === 1) {
                            let container_top = document.getElementById('id_answers_collection').offsetTop;
                            let container_height = document.getElementById('id_answers_collection').clientHeight;
                            let button_top = e.currentTarget.offsetTop;
                            let button_height = e.currentTarget.clientHeight;
                            let dropdown_content_element = dropdown_content_elements[0];
                            let menu_height = dropdown_content_element.clientHeight;

                            if ((button_top - container_top + button_height + menu_height) >= container_height) {
                                dropdown_content_element.style.top = e.currentTarget.offsetTop - 140 + "px";
                                dropdown_content_element.style.left = e.currentTarget.offsetLeft - e.currentTarget.nextElementSibling.clientWidth + e.currentTarget.clientWidth + 8 + "px";
                            } else {
                                dropdown_content_element.style.top = e.currentTarget.offsetTop + 27 + "px";
                                dropdown_content_element.style.left = e.currentTarget.offsetLeft - e.currentTarget.nextElementSibling.clientWidth + e.currentTarget.clientWidth + 8 + "px";
                            }
                        }

                    });
                    $('.answer_zones_dropdown_content').bind('mouseleave', function(e) {
                        var dropdown_menu_button = e.currentTarget.previousElementSibling;
                        if (dropdown_menu_button.classList.contains('fa-caret-up')) {
                            dropdown_menu_button.classList.remove('fa-caret-up');
                            dropdown_menu_button.classList.add('fa-caret-down');
                        }
                    });

                    $('input.option_checkbox').bind('click', function (e) {
                        let answerItemId = e.currentTarget.getAttribute('answer_item_id');
                        _fn.build.form.item.updateAnswerToZone(
                            parseInt(answerItemId), e.currentTarget.value, e.currentTarget.checked);

                        _fn.build.set_tab_editing_status();
                        _fn.build.refresh_save_button_status();
                    });

                    $element.find('.answer_text').bind('click', function (e) {
                        let range = document.createRange();
                        let selection = window.getSelection();

                        old_answer_text = e.currentTarget.textContent;
                        e.currentTarget.contentEditable = 'true';
                        range.selectNodeContents(e.currentTarget);
                        selection.removeAllRanges();
                        selection.addRange(range);
                        e.currentTarget.style.backgroundColor = '#fff';
                        e.currentTarget.focus();

                        $(e.target).unbind('focusout').focusout(function() {
                            let answer_item_id = parseInt(e.currentTarget.getAttribute('data-item_id'));
                            let new_answer_text = e.currentTarget.textContent;

                            e.currentTarget.textContent.contentEditable = 'false';
                            e.currentTarget.style.backgroundColor = '';

                            old_answer_text = old_answer_text || _fn.build.form.item.grabItemName();
                            e.currentTarget.textContent = new_answer_text || old_answer_text; // replace with new answer text on UI
                            var has_one = false;
                            _fn.build.form.item.itemObjects.forEach(function(item) {
                                if (item.displayName === new_answer_text) {
                                    has_one = true;
                                }
                            });
                            if (has_one === true) {
                                new_answer_text = old_answer_text;
                            }
                            // replacing in data
                            _fn.build.form.item.itemObjects.forEach(function(item) {
                                if (item.id === answer_item_id) {
                                    item.displayName = new_answer_text;
                                    e.currentTarget.textContent = new_answer_text;
                                }
                            });

                            _fn.build.set_tab_editing_status();
                            _fn.build.refresh_save_button_status();
                        });


                    });

                    $element.find('.delete_answer_button').bind('click', function(e) {
                        e.preventDefault();

                        let answer_item_id = parseInt(e.currentTarget.getAttribute('data-item_id'));
                        let answer_card = $('#id_answer_card__' + answer_item_id);

                        // remove this answer item from data
                        for (var i = 0; i <_fn.build.form.item.itemObjects.length; i++) {
                            let item = _fn.build.form.item.itemObjects[i];
                            if (item.id === answer_item_id) {
                                _fn.build.form.item.itemObjects.splice(i, 1);
                                // remove from UI
                                answer_card.remove();

                                _fn.build.set_tab_editing_status();
                                _fn.build.refresh_save_button_status();
                                break;
                            }
                        }
                    });

                    $('.answers_collection').sortable({
                        placeholder: 'placeholder-highlight',
                        start: function(event, ui) {
                            $('.answer_zones_dropdown_content').addClass('hidden');
                        },
                        stop: function(event, ui) {
                            var new_index = undefined;
                            var dragged_item_id = parseInt(ui.item[0].getAttribute('data-itemid'));
                            var answers_cards = $('.answer_item');

                            for (var i = 0; i < answers_cards.length; i++) {
                                if (dragged_item_id === parseInt($('.answer_item')[i].getAttribute('data-itemid'))) {
                                    new_index = i;
                                    break;
                                }
                            }

                            $('.answer_zones_dropdown_content').removeClass('hidden');

                            if (new_index === undefined) {
                                return;
                            }

                            _fn.build.set_tab_editing_status();
                            _fn.build.refresh_save_button_status();

                            for (var old_index = 0; old_index < _fn.build.form.item.itemObjects.length; old_index++) {
                                if (dragged_item_id === _fn.build.form.item.itemObjects[old_index].id) {
                                    if (new_index !== old_index) {
                                        if (new_index < old_index) {
                                            _fn.build.form.item.itemObjects.splice(
                                                new_index, 0, _fn.build.form.item.itemObjects[old_index]
                                            );
                                            _fn.build.form.item.itemObjects.splice(old_index + 1, 1);
                                        } else {
                                            _fn.build.form.item.itemObjects.splice(
                                                new_index + 1, 0, _fn.build.form.item.itemObjects[old_index]
                                            );
                                            _fn.build.form.item.itemObjects.splice(old_index, 1);
                                        }

                                        var last_card_id = answers_cards[answers_cards.length - 1].id;
                                        $('#id_add_answer_item_btn').insertAfter('#' + last_card_id);

                                        return;
                                    }
                                }
                            }

                            if (answers_cards.length > 0) {
                                var last_card_id = answers_cards[answers_cards.length - 1].id;
                                $('#id_add_answer_item_btn').insertAfter('#' + last_card_id);
                            }

                        }
                    });
                    $('.answers_collection').disableSelection();

                },

                set_tab_editing_status: function() {
                    var tab_id = _fn.selected_tab_id === undefined ? '0' : _fn.selected_tab_id;
                    _fn.tabs_editing_status[tab_id] = true;
                },

                refresh_save_button_status: function() {
                    var save_button = document.getElementsByClassName('save-button')[0];
                    var is_disabled = _fn.build.getEditingStatus()

                    if (!is_disabled) {
                        save_button.setAttribute('disabled', null);
                    } else if (is_disabled ){
                        save_button.removeAttribute('disabled');
                    }
                },

                clickHandlers: function() {
                    var $zoneTab = _fn.build.$el.zones.tab;
                    const $backgroundChoose = _fn.build.$el.backgroundChoose;

                    $element.find('.supported-setting-tags .tab input').bind('change', function() {
                        _fn.build.set_tab_editing_status();
                        _fn.build.refresh_save_button_status();
                    });
                    $element.find('.supported-setting-tags .tab textarea').bind('change', function() {
                        _fn.build.set_tab_editing_status();
                        _fn.build.refresh_save_button_status();
                    });
                    $element.find('.switcher').bind('click', function() {
                        _fn.build.set_tab_editing_status();
                        _fn.build.refresh_save_button_status();
                    });
                    $element.find('.resizable_box .zone_title .title_edit_button').bind('click', function() {
                        _fn.build.set_tab_editing_status();
                        _fn.build.refresh_save_button_status();
                    });

                    $element.find('.supported-setting-tags-nav > li').bind('click', function() {
                        var tabObj = $(this);
                        var tabID = tabObj.attr('id');

                        // Show hightlight if this tab button is disabled :
                        // If var. `target_img_expanded_url` defined & type_id is null, that also means the data is Old version. To be compatible with this format.
                        if (tabID === '2' && ((_fn.type_id === undefined || _fn.type_id === null) && _fn.target_img_expanded_url === null) ) {
                            if (!tabObj.hasClass('disable-section-hightlight')) {
                                tabObj.addClass('disable-section-hightlight');
                            }
                            setTimeout(function() {
                                tabObj.removeClass('disable-section-hightlight');
                            }, 500);

                            return;
                        }
                        if (tabID === '3' &&
                            ((_fn.build.form.zone.zoneObjects === undefined || _fn.build.form.zone.zoneObjects.length === 0) && (_fn.data.zones === undefined || _fn.data.zones.length === 0))
                        ) {
                            if (!tabObj.hasClass('disable-section-hightlight')) {
                                tabObj.addClass('disable-section-hightlight');
                            }
                            setTimeout(function() {
                                tabObj.removeClass('disable-section-hightlight');
                            }, 500);

                            return;
                        }
                        _fn.build.refreshTabsStatus(false, tabID);

                        if (!tabObj.hasClass('active-section')) {
                            tabObj.addClass('active-section');
                        }
                        _fn.build.selectTabPage(tabID);

                    });

                    $element.find('.save-button').bind('click', function(e) {
                        e.preventDefault();

                        if (e.currentTarget.hasAttribute('disabled')) {
                            return;
                        }

                        var tabID = _fn.selected_tab_id === undefined ? '0' : _fn.selected_tab_id;

                        if (!_fn.build.validate(tabID)) {
                            return;
                        }

                        _fn.build.form.submit(tabID, continue_mode=false);

                        _fn.tabs_editing_status[tabID] = false;

                        var root_div = document.getElementById('tmp_root');
                        if (root_div != null) {
                            document.getElementById('tmp_root').id = 'root';
                        }
                    })

                    $element.find('.add_answer_button').bind('click', function(e) {
                        e.preventDefault();

                        _fn.build.form.item.createAnswerItem({}, true);
                        _fn.build.rebind_events_for_answers_tab();
                        _fn.build.refreshTabsStatus();  // redraw tabs

                        _fn.build.set_tab_editing_status();
                        _fn.build.refresh_save_button_status();
                    });

                    $backgroundChoose.templates
                        .on('click', '.pattern-item', _fn.build.backgroundTemplateChoose);

                    $zoneTab
                        .on('click', '#id_add_zone_bt', function(e) {
                            let canvas = $(ID_AUTHOR_CANVAS)[0];
                            let left = canvas.offsetWidth / 100 * 40;
                            let top = canvas.offsetHeight / 100 * 45;

                            _fn.build.form.zone.makeResizableZone({x: left, y: top, width: 200, height: 100});
                            _fn.build.refreshTabsStatus();  // redraw tabs

                            _fn.build.set_tab_editing_status();
                            _fn.build.refresh_save_button_status();
                        });
                },
                form: {
                    zone: {
                        totalZonesCreated: 0,   // This counter is used for HTML IDs. Never decremented.
                        zoneObjects: [],        // The Editing version of Zones
                        generateNewZoneTitle: function() {
                            /**
                             * Guarantee generating a new unique Zone title.
                             */
                            for (var i = 1; true; i++) {
                                var has_one = false;
                                var new_unique_zone_title = gettext("Zone") + " " + i;
                                _fn.build.form.zone.zoneObjects.forEach(function(zone) {
                                    if (new_unique_zone_title === zone.title) {
                                        has_one = true;
                                    }
                                })

                                if (false === has_one) {
                                    return new_unique_zone_title;
                                }
                            }

                        },
                        add: function(oldZone) {
                            if (!oldZone) oldZone = {};

                            // Update zone obj
                            var zoneObj = {
                                title: oldZone.title || _fn.build.form.zone.generateNewZoneTitle(),
                                description: oldZone.description,
                                // uid: unique ID for this zone. For backwards compatibility,
                                // this field cannot be called "id" and must inherit the "title"
                                // property if no 'uid' value is present, since old versions of
                                // this block used the title as the primary identifier.
                                uid: oldZone.uid || oldZone.title || _fn.build.form.zone.generateUID(),
                                width: oldZone.width || 200,
                                height: oldZone.height || 100,
                                x: oldZone.x || 0,
                                y: oldZone.y || 0,
                                align: oldZone.align || 'none'
                            };

                            _fn.build.form.zone.zoneObjects.push(zoneObj);
                        },
                        generateUID: function() {
                            /**
                             * @brief       Generating a `uuid` for a new zone.
                             * @note        The previous of this method generating UID rely on the value of `_fn.build.form.zone.zoneObjects.length`.
                             *              And this is not safe because the `length` of array may depened on the logic of code. ( For example: this
                             *              array cleaned by some code, but the `uid_zone_{number}` will be still recovered from somewhere later`.
                             */
                            return (Date.now().toString(36) + Math.random().toString(36)).replace('.', '_');
                        },
                        makeReadonlyZone: function(oldZone, id_zones_canvas=ID_PREVIEW_CANVAS) {
                            let element = document.createElement('div');
                            let new_div_title = document.createElement('div');
                            let zone_left = (oldZone.x || 0);
                            let zone_top = (oldZone.y || 0);
                            let zone_width = oldZone.width || 200;
                            let zone_height = oldZone.height || 100;

                            element.setAttribute('id', oldZone.uid);
                            element.setAttribute( 'class', 'readonly_zone_box' );
                            element.setAttribute('style',`width:${zone_width}px; height:${zone_height}px; left:${zone_left}px; top:${zone_top}px`);
                            new_div_title.setAttribute('class', 'readonly_zone_title');
                            new_div_title.innerText = gettext(oldZone.title);

                            element.appendChild(new_div_title);
                            $(id_zones_canvas)[0].appendChild(element);
                        },
                        makeResizableZone: function(oldZone, id_zones_canvas=ID_AUTHOR_CANVAS) {
                            /**
                             * @brief                   Generating Zone on Page & adding zone record into Data. But if the `zone.uid`
                             *                          exists already in cache. This method return before creating.
                             * @dict    oldZone         zone object, if field `uid` doesn't exist in it. We generate a new uid and add this zone into data
                             *                          Then draw this zone on the page.
                             * @string  id_zones_canvas the element id where the new zones will be added on
                             */
                            let element = document.createElement('div');
                            let new_div_title = document.createElement('div');
                            let title_text = document.createElement('div');
                            let title_edit_icon = document.createElement('i');
                            let title_icon_container = document.createElement('div');
                            let zone_title = gettext(oldZone.title) || _fn.build.form.zone.generateNewZoneTitle();
                            let zone_uid = oldZone.uid || _fn.build.form.zone.generateUID();
                            let zone_align = oldZone.align || 'none';
                            let zone_left = oldZone.x || 0;
                            let zone_top = oldZone.y || 0;
                            let minWidth = 116;
                            let minHeight = 66;
                            let zone_width = oldZone.width || 200;
                            let zone_height = oldZone.height || 100;
                            let size = oldZone.size || 20;
                            let is_resizing = false;    // true: allow resizing zone | false: allow moving zone

                            element.setAttribute('id', zone_uid);
                            if (_fn.data.displayBorders !== true) {
                                element.setAttribute('class', 'resizable_box no-border')
                            } else {
                                element.setAttribute( 'class', 'resizable_box' );
                            }
                            element.setAttribute('style',`width:${zone_width}px; height:${zone_height}px; left:${zone_left}px; top:${zone_top}px`);
                            new_div_title.setAttribute('class', 'zone_title');

                            title_text.setAttribute('class', 'title_text');
                            title_text.innerText = zone_title;

                            title_edit_icon.setAttribute('class', 'fa-solid fa-pen-circle');
                            title_icon_container.setAttribute('class', 'title_edit_button');

                            title_icon_container.appendChild(title_edit_icon);
                            new_div_title.appendChild(title_icon_container);
                            new_div_title.appendChild(title_text);
                            element.appendChild(new_div_title);
                            $(id_zones_canvas)[0].appendChild(element);

                            // Support moving Resizable Box
                            var isDown = false;
                            var isEditTitle = false;
                            var oldZoneTitleText = title_text.textContent;
                            var offset = [0, 0];
                            element.addEventListener('mousedown', function(e) {
                                is_resizing = false;
                                isDown = true;
                                offset = [
                                    element.offsetLeft - e.clientX,
                                    element.offsetTop - e.clientY
                                ];

                                document.addEventListener('mouseup', function() {
                                    isDown = false;
                                    if (element.offsetWidth !== 0 && element.offsetHeight !== 0) {
                                        update_zones_data(element);

                                        _fn.build.set_tab_editing_status();
                                        _fn.build.refresh_save_button_status();
                                    }
                                    document.removeEventListener("mouseup", arguments.callee);
                                }, true);

                            }, true);

                            document.addEventListener('mousemove', function(event) {
                                if (is_resizing || isEditTitle) {
                                    return;
                                }
                                event.preventDefault();
                                if (isDown) {
                                    mousePosition = {
                                        x : event.clientX,
                                        y : event.clientY
                                    };
                                    var new_left = mousePosition.x + offset[0];
                                    var new_top = mousePosition.y + offset[1];
                                    var canvas_width = $('#id_author_canvas').width();
                                    var canvas_height = $('#id_author_canvas').height();
                                    if (new_left >= 0 && (new_left + element.offsetWidth) <= canvas_width) {
                                        element.style.left = new_left + 'px';
                                    }
                                    if (new_top >= 0 && (new_top + element.offsetHeight) <= canvas_height) {
                                        element.style.top = new_top + 'px';
                                    }
                                }
                            }, true);

                            title_icon_container.addEventListener('click', function(e) {
                                e.preventDefault();
                                isEditTitle = true;
                                title_text.contentEditable = 'true';
                                let range = document.createRange();
                                range.selectNodeContents(title_text);
                                let selection = window.getSelection();
                                selection.removeAllRanges();
                                selection.addRange(range);
                                title_text.style.backgroundColor = '#fff';
                                title_text.style.cursor = 'text';
                                title_text.focus();
                            });

                            title_text.addEventListener('focusout', function (e) {
                                e.preventDefault();
                                const _titleText = e.currentTarget;
                                isEditTitle = false;
                                _titleText.contentEditable = 'false';
                                _titleText.style.backgroundColor = "";
                                _titleText.style.cursor = 'move';

                                if (oldZoneTitleText !== _titleText.textContent) {
                                    var has_one = false;
                                    var zoneObjects = _fn.build.form.zone.zoneObjects;
                                    var zoneIndex = null;
                                    for (var i=0;i<zoneObjects.length;i++) {
                                        if (oldZoneTitleText === zoneObjects[i].title) {
                                            // current editing zone index
                                            zoneIndex = i;
                                        }
                                        if (_titleText.textContent === zoneObjects[i].title) {
                                            // check new zone title existing
                                            has_one = true;
                                        }
                                    }
                                    if (false === has_one) {
                                        if (zoneIndex !== null) {
                                            // new zone tile to zoneObject title
                                            if (oldZoneTitleText === zoneObjects[zoneIndex].title) {
                                                zoneObjects[zoneIndex].title = _titleText.textContent;
                                                oldZoneTitleText = _titleText.textContent;
                                            }
                                        }
                                    } else {
                                        // zone title duplicated revert changes
                                        _titleText.textContent = oldZoneTitleText;
                                    }
                                }
                            });

                            // We add new record into list if creating a new zone
                            if (oldZone.uid === undefined) {
                                _fn.build.form.zone.add({
                                    uid: zone_uid, title: zone_title,
                                    width: zone_width, height: zone_height,
                                    x: zone_left, y: zone_top, align: zone_align,
                                    description: oldZone.description
                                });
                            }

                            const top = document.createElement('div');
                            top.style.width = '100%';
                            top.style.height = size + 'px';
                            top.style.backgroundColor = 'transparent';
                            top.style.position = 'absolute';
                            top.style.top = - (size/2) + 'px';
                            top.style.left = '0px';
                            top.style.cursor = 'ns-resize';

                            top.addEventListener('mousedown', resizeYNegative());

                            element.appendChild(top);

                            const bottom = document.createElement('div');
                            bottom.style.width = '100%';
                            bottom.style.height = size + 'px';
                            bottom.style.backgroundColor = 'transparent';
                            bottom.style.position = 'absolute';
                            bottom.style.bottom = - (size/2) + 'px';
                            bottom.style.left = '0px';
                            bottom.style.cursor = 'ns-resize';

                            bottom.addEventListener('mousedown',resizeYPositive())

                            element.appendChild(bottom);

                            const left = document.createElement('div');
                            left.style.width = size + 'px';
                            left.style.height = '100%';
                            left.style.backgroundColor = 'transparent';
                            left.style.position = 'absolute';
                            left.style.top = '0px';
                            left.style.left = - (size/2) + 'px';
                            left.style.cursor = 'ew-resize';

                            left.addEventListener('mousedown', resizeXNegative());

                            element.appendChild(left);

                            const right = document.createElement('div');
                            right.style.width = size + 'px';
                            right.style.height = '100%';
                            right.style.backgroundColor = 'transparent';
                            right.style.position = 'absolute';
                            right.style.top = '0px';
                            right.style.right = - (size/2) + 'px';
                            right.style.cursor = 'ew-resize';

                            right.addEventListener('mousedown',resizeXPositive());

                            element.appendChild(right);

                            const corner1 = document.createElement('div');
                            corner1.style.width = '10px';
                            corner1.style.height = '10px';
                            corner1.style.backgroundColor = '#ffffff';
                            corner1.style.position = 'absolute';
                            corner1.style.top = '-5px';
                            corner1.style.left = '-5px';
                            corner1.style.cursor = 'nw-resize';
                            corner1.style.border = '1px solid #000000';

                            corner1.addEventListener('mousedown', resizeXNegative());
                            corner1.addEventListener('mousedown', resizeYNegative());

                            element.appendChild(corner1);

                            // It's a remove button.
                            const corner2 = document.createElement('i');
                            corner2.setAttribute('id', 'id_remove_zone');
                            corner2.setAttribute('class', 'fa-solid fa-circle-minus');
                            corner2.setAttribute('style', 'color: #f50000;');
                            corner2.style.width = '16px';
                            corner2.style.height = '16px';
                            corner2.style.position = 'absolute';
                            corner2.style.top = '-9px';
                            corner2.style.right = '-8px';
                            corner2.style.cursor = 'pointer';

                            corner2.addEventListener('mousedown', resizeXPositive());
                            corner2.addEventListener('mousedown', resizeYNegative());
                            corner2.addEventListener('click', removeZone);

                            element.appendChild(corner2);

                            const corner3 = document.createElement('div');
                            corner3.style.width = '10px';
                            corner3.style.height = '10px';
                            corner3.style.backgroundColor = '#ffffff';
                            corner3.style.position = 'absolute';
                            corner3.style.bottom = '-5px';
                            corner3.style.left = '-5px';
                            corner3.style.cursor = 'sw-resize';
                            corner3.style.border = '1px solid #000000';

                            corner3.addEventListener('mousedown',resizeXNegative());
                            corner3.addEventListener('mousedown',resizeYPositive());

                            element.appendChild(corner3);

                            const corner4 = document.createElement('div');
                            corner4.style.width = '10px';
                            corner4.style.height = '10px';
                            corner4.style.backgroundColor = '#ffffff';
                            corner4.style.position = 'absolute';
                            corner4.style.bottom = '-5px';
                            corner4.style.right = '-5px';
                            corner4.style.cursor = 'se-resize';
                            corner4.style.border = '1px solid #000000';

                            corner4.addEventListener('mousedown', resizeXPositive())
                            corner4.addEventListener('mousedown', resizeYPositive())

                            element.appendChild(corner4);

                            function update_zones_data(resizable_rect) {
                                let zone_uid = resizable_rect.id;
                                let pos = $('#' + zone_uid).position();

                                _fn.build.form.zone.zoneObjects.forEach(function(zoneObj) {
                                    if (zoneObj.uid === zone_uid) {
                                        zoneObj.x = pos.left;
                                        zoneObj.y = pos.top;
                                        zoneObj.width = resizable_rect.offsetWidth;
                                        zoneObj.height = resizable_rect.offsetHeight;
                                    }
                                });
                            }

                            function get_int_style(key) {
                                return parseInt(window.getComputedStyle(element).getPropertyValue(key));
                            }

                            function resizeXPositive() {
                                let offsetX
                                function dragMouseDown(e) {
                                    is_resizing = true;     // Flag: disable event handler of container
                                    if(e.button !== 0) return
                                    e = e || window.event;
                                    e.preventDefault();
                                    const {clientX} = e;
                                    offsetX = clientX - element.offsetLeft - get_int_style('width');
                                    document.addEventListener('mouseup', closeDragElement)
                                    document.addEventListener('mousemove', elementDrag)
                                  }

                                  function elementDrag(e) {
                                        const {clientX} = e;
                                        let x = clientX - element.offsetLeft - offsetX;
                                        var new_right = x + element.offsetLeft;
                                        var canvas_width = $('#id_author_canvas').width();
                                        var title_zone_width = new_div_title.clientWidth + 12;
                                        if (new_right > canvas_width || x < title_zone_width) {
                                            return;
                                        }
                                        if(x < minWidth) x = minWidth;
                                        element.style.width =  x + 'px';
                                  }

                                  function closeDragElement() {
                                    update_zones_data(element);

                                    document.removeEventListener("mouseup", closeDragElement);
                                    document.removeEventListener("mousemove", elementDrag);

                                    _fn.build.set_tab_editing_status();
                                    _fn.build.refresh_save_button_status();
                                  }
                                return dragMouseDown
                            }

                            function resizeYPositive() {
                                let offsetY
                                function dragMouseDown(e) {
                                    is_resizing = true;     // Flag: disable event handler of container
                                    if(e.button !== 0) return
                                    e = e || window.event;
                                    e.preventDefault();
                                    const {clientY} = e;
                                    offsetY = clientY - element.offsetTop - get_int_style('height');

                                    document.addEventListener('mouseup',closeDragElement)
                                    document.addEventListener('mousemove',elementDrag)
                                  }

                                  function elementDrag(e) {
                                        const {clientY} = e;
                                        let y =  clientY - element.offsetTop - offsetY;
                                        var new_bottom = y + element.offsetTop;
                                        var canvas_height = $('#id_author_canvas').height();
                                        var title_zone_height = new_div_title.clientHeight + 12;
                                        if (new_bottom > canvas_height || y < title_zone_height) {
                                            return;
                                        }
                                        if(y < minHeight) y = minHeight;
                                        element.style.height = y + 'px';
                                  }

                                  function closeDragElement() {
                                    update_zones_data(element);

                                    document.removeEventListener("mouseup", closeDragElement);
                                    document.removeEventListener("mousemove", elementDrag);

                                    _fn.build.set_tab_editing_status();
                                    _fn.build.refresh_save_button_status();
                                  }
                                return dragMouseDown
                            }

                            function resizeXNegative() {
                                let offsetX
                                let startX
                                let startW
                                let maxX
                                function dragMouseDown(e) {
                                    is_resizing = true;     // Flag: disable event handler of container
                                    if(e.button !== 0) return
                                    e = e || window.event;
                                    e.preventDefault();
                                    const {clientX} = e;
                                    startX = get_int_style('left')
                                    startW = get_int_style('width')
                                    offsetX = clientX - startX;
                                    maxX = startX + startW - minWidth;

                                    document.addEventListener('mouseup',closeDragElement)
                                    document.addEventListener('mousemove',elementDrag)
                                  }

                                  function elementDrag(e) {
                                        const {clientX} = e;
                                        let x = clientX - offsetX;
                                        if (x < 0) {
                                            return;
                                        }
                                        let w = startW + startX - x;
                                        var title_zone_width = new_div_title.clientWidth + 12;
                                        if (w < title_zone_width) {
                                            return;
                                        }
                                        if(w < minWidth) w = minWidth;
                                        if(x > maxX) x = maxX;
                                        element.style.left = x + 'px';
                                        element.style.width = w + 'px';
                                  }

                                  function closeDragElement() {
                                    update_zones_data(element);

                                    document.removeEventListener("mouseup", closeDragElement);
                                    document.removeEventListener("mousemove", elementDrag);

                                    _fn.build.set_tab_editing_status();
                                    _fn.build.refresh_save_button_status();
                                  }
                                return dragMouseDown
                            }

                            function resizeYNegative() {
                                let offsetY
                                let startY
                                let startH
                                let maxY
                                function dragMouseDown(e) {
                                    is_resizing = true;     // Flag: disable event handler of container
                                    if(e.button !== 0) return
                                    e = e || window.event;
                                    e.preventDefault();
                                    const {clientY} = e;
                                    startY = get_int_style('top')
                                    startH = get_int_style('height')
                                    offsetY = clientY - startY;
                                    maxY = startY + startH - minHeight;

                                    document.addEventListener('mouseup',closeDragElement,false)
                                    document.addEventListener('mousemove',elementDrag,false)
                                  }

                                  function elementDrag(e) {
                                        const {clientY} = e;
                                        let y =  clientY - offsetY;
                                        var title_zone_height = new_div_title.clientHeight + 12;
                                        if (y < 0) {
                                            return;
                                        }
                                        let h = startH + startY - y;
                                        if (h < title_zone_height) {
                                            return;
                                        }
                                        if(h < minHeight) h = minHeight;
                                        if(y > maxY) y = maxY;
                                        element.style.top = y + 'px';
                                        element.style.height = h + 'px';
                                  }

                                  function closeDragElement() {
                                    update_zones_data(element);

                                    document.removeEventListener("mouseup", closeDragElement);
                                    document.removeEventListener("mousemove", elementDrag);

                                    _fn.build.set_tab_editing_status();
                                    _fn.build.refresh_save_button_status();
                                  }
                                return dragMouseDown
                            }

                            function removeZone(e) {
                                let zone_uid = e.currentTarget.parentElement.id;

                                // Remove zone from page
                                e.currentTarget.parentElement.remove();
                                // Find the uid of the zone in the array and remove it.
                                for (array_index = 0; array_index < _fn.build.form.zone.zoneObjects.length;
                                     array_index++) {
                                    if (_fn.build.form.zone.zoneObjects[array_index].uid == zone_uid) break;
                                }
                                _fn.build.form.zone.zoneObjects.splice(array_index, 1);

                                for (array_index = 0; array_index < _fn.data.zones.length; array_index++) {
                                    if (_fn.data.zones[array_index].uid == zone_uid) break;
                                }
                                _fn.data.zones.splice(array_index, 1);

                                // Remove related zones from Item in `_fn.data` if this zone is the removed one.
                                for (var i = 0; i< _fn.data.items.length; i++) {
                                    const item = _fn.data.items[i];
                                    if (item.zones.includes(zone_uid)) {
                                        item.zones.splice(item.zones.indexOf(zone_uid), 1);
                                    }
                                }

                                _fn.build.refreshTabsStatus();  // redraw tabs

                                _fn.build.set_tab_editing_status();
                                _fn.build.refresh_save_button_status();
                            }
                        }

                    },
                    item: {
                        count: 0,
                        itemObjects: [],    // The Editing version of Answer
                        predefinedZoneColors: [
                            'color: #00476A; background-color: #DEF4FF;',
                            'color: #7D19C9; background-color: #F4E4FF;',
                            'color: #56CF88; background-color: #56CF8833;',
                            'color: #FF776F; background-color: #FF776F33;',
                            'color: #FFC700; background-color: #FFC70033;',
                            'color: #0057D9; background-color: #0057D933;',
                            'color: #B8D312; background-color: #B8D31233;',
                            'color: #CD00DF; background-color: #CD00DF33;',
                            'color: #CD4A00; background-color: #CD4A0033;',
                            'color: #00A194; background-color: #00A19433;'
                        ],

                        grabAnswerId: function() {
                            // Generate and return new unique Item ID
                            for (var id = 1; true; id++) {
                                var has_one = false;

                                _fn.build.form.item.itemObjects.forEach(function(item) {
                                    if (id === item.id) {
                                        has_one = true;
                                    }
                                });

                                if (false === has_one) {
                                    return id;
                                }
                            }

                        },

                        grabItemName: function() {
                            for (let new_item_id = 0; new_item_id < $('.answer_item').length; new_item_id++) {
                                let has_one = false;
                                let new_generated_name = gettext('Answer') + ' ' + (1 + new_item_id);

                                _fn.build.form.item.itemObjects.forEach(function(item) {
                                    if (item.displayName === new_generated_name) {
                                        has_one = true;
                                    }
                                });

                                if (has_one === false) {
                                    return new_generated_name;
                                }
                            }

                            return 'Answer ' + (1 + $('.answer_item').length);
                        },

                        createAnswerItem: function(oldItem = {}, create_new_flag=false) {
                            let item_uid = oldItem.id === undefined ? _fn.build.form.item.grabAnswerId() : oldItem.id;
                            let item_title = gettext(oldItem.displayName) || _fn.build.form.item.grabItemName();
                            let item_zones = oldItem.zones || [];
                            let id_answer_name = 'id_answer_name__' + item_uid;
                            let id_answer_colored_zones = 'id_answer_colored_zones__' + item_uid;

                            let answer_element = $(`<div id="id_answer_card__${item_uid}" data-itemid="${item_uid}" class="answer_item"></div>`); // Answer Item Card
                            let options_menu = $('<div class="answer_zones_dropdown_content"></div>');
                            let options_list = $('<ul></ul>');
                            let handle_el = $('<div class="handler_style"></div>');
                            let handle_icon = $('<i class="fa-solid fa-grip-dots-vertical" style="color: #1D1D1D"></i>');
                            let answer_text = $(`<div class="answer_text" id="${id_answer_name}" data-item_id="${item_uid}">${item_title}</div>`);
                            let linked_zones = $(`<div class="selected_zones" id="${id_answer_colored_zones}"></div>`);
                            let dropdown_btn = $('<div class="answer_zones_dropdown_menu fa-solid fa-caret-down"></div>');

                            // Options Menu
                            _fn.build.form.zone.zoneObjects.forEach(function(zoneObj){
                                let option_zone = $(`<li id="${zoneObj.uid}" class="dropdown_item"></li>`);
                                let option_checkbox = document.createElement('input');
                                option_checkbox.setAttribute('class', 'option_checkbox');
                                option_checkbox.setAttribute('type', 'checkbox');
                                option_checkbox.setAttribute('value', zoneObj.uid);
                                option_checkbox.setAttribute('answer_item_id', item_uid);
                                if (item_zones.includes(zoneObj.uid)) {
                                    option_checkbox.setAttribute('checked', 'checked');
                                }
                                option_zone.append(option_checkbox);
                                let option_display_name = document.createElement('span');
                                option_display_name.setAttribute('class', 'option_display_name');
                                option_display_name.innerText = gettext(zoneObj.title);
                                option_zone.append(option_display_name);
                                options_list.append(option_zone);
                            });
                            var delete_the_answer = gettext('Delete the Answer');
                            options_list.append($(`<li data-item_id="${item_uid}" class="delete_answer_button">${delete_the_answer}</li>`));
                            options_menu.append(options_list);
                            // Card Icon
                            handle_el.append(handle_icon);
                            answer_element.append(handle_el);
                            // Answer description
                            answer_element.append(answer_text);
                            // Colored Selected Zones Bar of this answer
                            let item_used_zones_titles = [];
                            let zone_counter = 0;
                            _fn.build.form.zone.zoneObjects.forEach(function(zoneObj){
                                if (item_zones.includes(zoneObj.uid)) {
                                    var predefinedStyle = _fn.build.form.item.predefinedZoneColors[zone_counter % _fn.build.form.item.predefinedZoneColors.length];
                                    item_used_zones_titles.push({title: gettext(zoneObj.title), style: predefinedStyle});
                                }
                                zone_counter++;
                            });
                            if (item_used_zones_titles.length === 0) {
                                linked_zones.addClass('hidden');
                            } else {
                                item_used_zones_titles.forEach(function(zoneInfo) {
                                    let colored_used_zone_title = $(`<div class="colored_name" style="${zoneInfo.style}">${zoneInfo.title}</div>`);
                                    linked_zones.append(colored_used_zone_title);
                                })
                            }
                            answer_element.append(linked_zones);
                            answer_element.append(dropdown_btn);
                            answer_element.append(options_menu);    // Element `options_menu` has to be behind element `dropdown_btn`
                            // Insert this New Answer Item into Collection
                            answer_element.insertBefore('#id_add_answer_item_btn');

                            if (create_new_flag) {
                                // Add this new Answer Card into data
                                _fn.build.form.item.updateAnswerToZone(item_uid, undefined, true);
                            }
                        },
                        updateAnswerToZone: function(answerItemId, zoneId, addOrRemoveFlag) {
                            // Adding/Removing related zones to a Answer Card + Rendering Colored zones bar in the Answer Card
                            let updated_flag = false;
                            let zone_counter = 0;
                            let zone_title = undefined;
                            let zone_style = undefined;
                            var colored_zones_bar = $('#id_answer_colored_zones__' + answerItemId);

                            if (zoneId !== undefined) {
                                _fn.build.form.zone.zoneObjects.forEach(function (zone) {
                                    if (zone.uid == zoneId) {
                                        zone_title = zone.title;
                                        zone_style = _fn.build.form.item.predefinedZoneColors[zone_counter % _fn.build.form.item.predefinedZoneColors.length];
                                    }
                                    zone_counter++;
                                })
                                if (zone_title === undefined) {
                                    return;
                                }

                                _fn.build.form.item.itemObjects.forEach(function (item) {
                                    if (item.id === answerItemId) {
                                        updated_flag = true;

                                        if (addOrRemoveFlag === true) {
                                            // Link zone uid
                                            if (!item.zones.includes(zoneId)) {
                                                // add to data
                                                item.zones.push(zoneId);
                                                // add to UI
                                                colored_zones_bar.append($(`<div class="colored_name" style="${zone_style}">${zone_title}</div>`));
                                                // show colored zone names bar if need
                                                if (colored_zones_bar.hasClass('hidden')) {
                                                    colored_zones_bar.removeClass('hidden');
                                                }
                                            }
                                        } else {
                                            // Unlink zone uid
                                            if (item.zones.includes(zoneId)) {
                                                // remove from data
                                                item.zones.splice(item.zones.indexOf(zoneId), 1);
                                                // remove from UI
                                                colored_zones_bar.children('.colored_name').each(function (idx, colored_name_el) {
                                                    if (colored_name_el.innerText === zone_title) {
                                                        colored_name_el.remove();
                                                    }
                                                });
                                                // hide colored zone names bar if need
                                                if (colored_zones_bar.children('.colored_name').length === 0) {
                                                    if (!colored_zones_bar.hasClass('hidden')) {
                                                        colored_zones_bar.addClass('hidden');
                                                    }
                                                }
                                            }
                                        }
                                    }
                                });
                            }

                            if ((updated_flag === false && addOrRemoveFlag === true) || zoneId === undefined) {
                                var name_el_id = 'id_answer_name__' + answerItemId; // answer name element Format: `id_answer_name__` + item_id

                                // add New Item Object to data while link a zone with the Item at first time.
                                // That also means that we don't add data into `itemObjects` for a just created Item linked with nothing of zones.
                                var data = {
                                    displayName: document.getElementById(name_el_id).innerText || ('Answer ' + (1 + $('.answer_item').length)),
                                    zones: zoneId === undefined ? [] : [zoneId],
                                    id: answerItemId,
                                    feedback: {correct: '', incorrect: ''},
                                    imageURL: 'imageURL',
                                    imageDescription: 'imageDescription',
                                };
                                _fn.build.form.item.itemObjects.push(data);

                                if (zoneId !== undefined) {
                                    // add to UI
                                    colored_zones_bar.append($(`<div class="colored_name">${zone_title}</div>`));
                                    // show colored zone names bar
                                    if (colored_zones_bar.hasClass('hidden')) {
                                        colored_zones_bar.removeClass('hidden');
                                    }
                                }
                            }
                        },
                    },
                    background_check(oldAssetId, callback) {
                        /**
                         * Handle check and delete unused custom background asset
                         */
                        const data = {
                            asset_id: oldAssetId
                        }
                        var handlerUrl = runtime.handlerUrl(element, 'background_check');
                        $.post(handlerUrl, JSON.stringify(data), 'json')
                            .done(function(response) {
                                if (response.result === 'success') {
                                    // runtime.notify('save', continue_mode ? {state: 'save_and_continue'} : {state: 'end'});
                                } else {
                                    var result = response.result;
                                    runtime.notify('error', {
                                        'title': window.gettext("There was an error with your form."),
                                        'message': result
                                    });
                                }
                            })
                            .always(function() {
                                if (callback) {
                                    callback.apply(this);
                                }
                            });
                    },
                    submit: function(tabID, continue_mode=false) {
                        // Save parts of data for a specified Tab
                        var post_data = {};

                        // tabID '0'
                        post_data['display_name'] = $element.find('.display-name').val();
                        post_data['weight'] = $element.find('.weight').val();
                        post_data['max_attempts'] = $element.find(".max-attempts").val();
                        post_data['problem_text'] = $element.find('.problem-text').val();
                        post_data['feedback'] = {'finish': $element.find('.final-feedback').val()};
                        // tabID '1'
                        post_data['type_id'] = parseInt(_fn.type_id);
                        post_data['custom_background'] = _fn.custom_background;
                        // Apply new selected template data to `_fn.data.zones/items` if user clicking save button
                        // of Background Tab directly before he switch to Zones / Items Tab.
                        if (_fn.new_selected_tpl_data !== undefined) {
                            _fn.data.zones = _fn.data.zones.concat(_fn.new_selected_tpl_data.zones);
                            _fn.data.items = _fn.data.items.concat(_fn.new_selected_tpl_data.items);
                            _fn.new_selected_tpl_data = undefined;
                        }
                        // tabID '2' or '3'
                        if (_fn.build.form.item.itemObjects.length > 0) {
                            _fn.data.items = _fn.build.form.item.itemObjects;
                        }
                        if (_fn.build.form.zone.zoneObjects.length > 0) {
                            _fn.data.zones = _fn.build.form.zone.zoneObjects;
                        }
                        post_data['type_id'] = parseInt(_fn.type_id);           // Have to save this data assigned in Background Tab again
                        post_data['custom_background'] = _fn.custom_background; // Save again

                        post_data['data'] = _fn.data;

                        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');

                        runtime.notify('save', {state: 'start', message: gettext("Saving")});

                        $.post(handlerUrl, JSON.stringify(post_data), 'json').done(function(response) {
                            if (response.result === 'success') {
                                runtime.notify('save', continue_mode ? {state: 'save_and_continue'} : {state: 'end'});
                            } else {
                                var message = response.messages.join(", ");
                                runtime.notify('error', {
                                    'title': window.gettext("There was an error with your form."),
                                    'message': message
                                });
                            }
                        });

                    }
                }
            },

            data: null
        };

        return {
            init: _fn.build.init
        };
    })(jQuery);

    $element.find('.cancel-button').bind('click', function(e) {
        e.preventDefault();
        runtime.notify('cancel', {});

        var root_div = document.getElementById('tmp_root');
        if (root_div != null) {
            document.getElementById('tmp_root').id = 'root';
        }
    });

    // Initialize js component
    const loadImageSize = path => {
      return new Promise((resolve, reject) => {
        const img = new Image()
        img.crossOrigin = 'Anonymous' // to avoid CORS if used with Canvas
        img.src = path
        img.onload = () => {
            zones_tab_bk_image_width = img.width;
            zones_tab_bk_image_height = img.height;
            resolve(img);
        }
        img.onerror = e => {
          reject(e)
        }
      })
    }

    if (params.is_old_version === true) {
        try {
            await loadImageSize(params.target_img_expanded_url)
        } catch (e) {
            console.log(e)
        }
    }

    dragAndDrop.init();

}
