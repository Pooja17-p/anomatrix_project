// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SecurityAudit {
    struct AuditLog {
        string user_id;
        string event_type;
        uint256 timestamp;
        string ip_address;
        string city;
        string country;
        string risk_level;
        string auth_method;
        string login_status;
    }

    AuditLog[] public logs;
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function addAuditLog(
        string memory _user_id,
        string memory _event_type,
        uint256 _timestamp,
        string memory _ip_address,
        string memory _city,
        string memory _country,
        string memory _risk_level,
        string memory _auth_method,
        string memory _login_status
    ) public onlyOwner returns (uint256) {
        logs.push(AuditLog({
            user_id: _user_id,
            event_type: _event_type,
            timestamp: _timestamp,
            ip_address: _ip_address,
            city: _city,
            country: _country,
            risk_level: _risk_level,
            auth_method: _auth_method,
            login_status: _login_status
        }));
        return logs.length - 1;
    }

    function getAuditLog(uint256 index) public view returns (
        string memory user_id,
        string memory event_type,
        uint256 timestamp,
        string memory ip_address,
        string memory city,
        string memory country,
        string memory risk_level,
        string memory auth_method,
        string memory login_status
    ) {
        require(index < logs.length, "Index out of bounds");
        AuditLog memory log = logs[index];
        return (
            log.user_id,
            log.event_type,
            log.timestamp,
            log.ip_address,
            log.city,
            log.country,
            log.risk_level,
            log.auth_method,
            log.login_status
        );
    }

    function getAuditLogsByUser(string memory _user_id) public view returns (uint256[] memory) {
        uint256 count = 0;
        for (uint256 i = 0; i < logs.length; i++) {
            if (keccak256(bytes(logs[i].user_id)) == keccak256(bytes(_user_id))) {
                count++;
            }
        }

        uint256[] memory userLogIndices = new uint256[](count);
        uint256 index = 0;
        for (uint256 i = 0; i < logs.length; i++) {
            if (keccak256(bytes(logs[i].user_id)) == keccak256(bytes(_user_id))) {
                userLogIndices[index] = i;
                index++;
            }
        }
        return userLogIndices;
    }

    function getTotalLogs() public view returns (uint256) {
        return logs.length;
    }
}
