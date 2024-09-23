/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component,useState,onWillStart } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import {_t} from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

class SystrayIcon extends Component {
 setup() {
   super.setup(...arguments);
   this.action = useService("action");
   this.state = useState({weather_data :[],weather:{} })
   this.dialogService = useService("dialog");
 }

 async _onClick() {
     var self = this;
    this.action.doAction({
        name: 'Help form',
        res_model: 'help.icons',
        views: [[false, 'form']],
        type: 'ir.actions.act_window',
        view_mode: 'form',
        target: 'new'
    });
 }
}
SystrayIcon.template = "systray_icon";
SystrayIcon.components = {Dropdown};
export const systrayItem = {
 Component: SystrayIcon,
};
 registry.category("systray").add("SystrayIcon", systrayItem, { sequence: 1 });


