local function auto_field_name(str)
	if str == nil or str == "" then
		return str
	else
		local first_char = string.lower(string.sub(str, 1, 1))
		local rest_of_string = string.sub(str, 2)
		return first_char .. rest_of_string
	end
end

return {
	auto_field_name = auto_field_name,
}
